#!/usr/bin/env python3
"""Mede o tempo interno do DuckDB e as cardinalidades estimada e real de cada operador."""

import json
import re
import statistics
from collections import Counter
from pathlib import Path

import duckdb
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "datalake" / "nlst.duckdb"
QUERIES = ROOT / "experiments" / "queries"
RESULTS = ROOT / "experiments" / "results"
PROFILES = ROOT / "experiments" / "profiles"
N_ROUNDS = 10


def to_int(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    digits = re.sub(r"[^\d]", "", str(value))
    return int(digits) if digits else None


def walk(node, rows, depth=0):
    name = node.get("operator_name") or node.get("operator_type") or ""
    extra = node.get("extra_info") or {}
    estimated = None
    if isinstance(extra, dict):
        for key, value in extra.items():
            if "estimated" in key.lower():
                estimated = to_int(value)
    if name:
        rows.append({
            "depth": depth,
            "operator": name.strip(),
            "estimated": estimated,
            "actual": to_int(node.get("operator_cardinality")),
        })
    for child in node.get("children", []):
        walk(child, rows, depth + 1)


def main():
    PROFILES.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    con.execute("SET enable_profiling = 'json'")

    times, cards = [], []
    for sql_file in sorted(QUERIES.glob("*.sql")):
        qid = sql_file.stem
        sql = sql_file.read_text()
        out = PROFILES / f"{qid}.json"
        con.execute(f"SET profiling_output = '{out}'")

        latencies = []
        for i in range(N_ROUNDS + 1):          # a primeira execução é aquecimento
            con.execute(sql).fetchall()
            profile = json.loads(out.read_text())
            if i > 0:
                latencies.append(float(profile["latency"]) * 1000)

        times.append({
            "query_id": qid,
            "engine_mean_ms": round(statistics.mean(latencies), 2),
            "engine_std_ms": round(statistics.stdev(latencies), 2),
            "engine_min_ms": round(min(latencies), 2),
        })

        ops = []
        walk(profile, ops)
        for op in ops:
            est, act = op["estimated"], op["actual"]
            q = round(max(est / act, act / est), 2) if est and act else None
            cards.append({"query_id": qid, **op, "q_error": q,
                          "is_join": "JOIN" in op["operator"].upper()})
        print(f"  {qid}: {times[-1]['engine_mean_ms']} ms no motor")

    con.close()

    eng = pl.DataFrame(times)
    card = pl.DataFrame(cards)
    client = pl.read_parquet(RESULTS / "experiment_results.parquet").select(
        "query_id", (pl.col("mean_time_s") * 1000).round(2).alias("client_mean_ms"))
    eng = eng.join(client, on="query_id").with_columns(
        (pl.col("client_mean_ms") / pl.col("engine_mean_ms")).round(1).alias("client_vs_engine"),
        (100 * (1 - pl.col("engine_mean_ms") / pl.col("client_mean_ms"))).round(1)
            .alias("overhead_pct"))

    eng.write_csv(RESULTS / "engine_times.csv")
    card.write_csv(RESULTS / "cardinality.csv")

    pl.Config(tbl_rows=-1, tbl_cols=-1, fmt_str_lengths=40)
    print("\n== Tempo no motor vs. no cliente ==")
    print(eng)

    joins = card.filter(pl.col("is_join"))
    print("\n== Junções: cardinalidade estimada vs. real ==")
    print(joins.select("query_id", "depth", "operator", "estimated", "actual", "q_error"))
    if joins["estimated"].null_count() == joins.height:
        print(f"\nATENÇÃO: nenhuma estimativa encontrada. Mande o arquivo {PROFILES / 'E3-Q1.json'}")

    print("\n== Operadores de junção usados ==")
    print(Counter(joins["operator"].to_list()))

    print("\n== E3: as duas versões de cada par têm as mesmas junções? ==")
    for a, b in [("E3-Q1", "E3-Q2"), ("E3-Q3", "E3-Q4"), ("E3-Q5", "E3-Q6"), ("E3-Q7", "E3-Q8")]:
        sig = lambda q: sorted(joins.filter(pl.col("query_id") == q)
                               .select("operator", "actual").rows())
        print(f"  {a} x {b}: {'iguais' if sig(a) == sig(b) else 'DIFERENTES'}")


if __name__ == "__main__":
    main()