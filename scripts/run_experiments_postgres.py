#!/usr/bin/env python3
"""
PostgreSQL experiments: forced JOIN algorithms and forced JOIN order.
Complements the DuckDB experiments by testing what DuckDB cannot.
"""

import json
import sys
import time
from pathlib import Path

import psycopg

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"
PLANS_DIR = PROJECT_ROOT / "experiments" / "plans_pg"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PLANS_DIR.mkdir(parents=True, exist_ok=True)

PG_CONNSTR = "dbname=nlst port=5433 host=/tmp"
N_ROUNDS = 10

# ── Queries to test ──────────────────────────────────────────

# Two representative queries: a 2-table join (large) and a 3-table join
Q_2TABLE = """
SELECT m.patient_id, m.slide_id, lc.modality, lc.timepoint
FROM masterfile m
JOIN lung_cancer lc ON m.patient_id = lc.patient_id
"""

Q_3TABLE = """
SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality
FROM pathology p
JOIN masterfile m ON p.slide_id = m.slide_id
JOIN lung_cancer lc ON m.patient_id = lc.patient_id
"""

# E3 order pairs (natural vs reversed)
Q_3TABLE_REV = """
SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality
FROM lung_cancer lc
JOIN masterfile m ON lc.patient_id = m.patient_id
JOIN pathology p ON m.slide_id = p.slide_id
"""

Q_4TABLE = """
SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality, t.treatment_category
FROM pathology p
JOIN masterfile m ON p.slide_id = m.slide_id
JOIN lung_cancer lc ON m.patient_id = lc.patient_id
JOIN treatment t ON m.patient_id = t.patient_id
"""

Q_4TABLE_REV = """
SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality, t.treatment_category
FROM lung_cancer lc
JOIN treatment t ON lc.patient_id = t.patient_id
JOIN masterfile m ON lc.patient_id = m.patient_id
JOIN pathology p ON m.slide_id = p.slide_id
"""


def run_query(con, sql, label, settings=None):
    """Run a query N_ROUNDS times and collect EXPLAIN ANALYZE."""
    if settings:
        for s in settings:
            con.execute(s)

    # Warm up
    con.execute(sql).fetchall()

    # EXPLAIN ANALYZE (JSON)
    plan_rows = con.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}").fetchone()
    plan = plan_rows[0]
    (PLANS_DIR / f"{label}.json").write_text(json.dumps(plan, indent=2))

    # Extract algorithm and estimated/actual rows from top node
    top = plan[0]["Plan"]
    algo = top.get("Node Type", "?")
    est = top.get("Plan Rows", 0)
    act = top.get("Actual Rows", 0)
    engine_ms = top.get("Actual Total Time", 0)

    # Timing
    times = []
    for _ in range(N_ROUNDS):
        t0 = time.perf_counter()
        con.execute(sql).fetchall()
        times.append((time.perf_counter() - t0) * 1000)

    mean_t = sum(times) / len(times)
    std_t = (sum((t - mean_t) ** 2 for t in times) / len(times)) ** 0.5

    print(f"  {label:40s} | {algo:20s} | {mean_t:>8.1f} ms ± {std_t:>6.1f} | "
          f"est={est:>10,} act={act:>10,} | engine={engine_ms:.1f} ms")

    return {
        "label": label, "algorithm": algo,
        "mean_ms": round(mean_t, 2), "std_ms": round(std_t, 2),
        "min_ms": round(min(times), 2),
        "estimated_rows": est, "actual_rows": act,
        "engine_ms": round(engine_ms, 2),
        "settings": settings or [],
    }


def main():
    print("=" * 110)
    print("POSTGRESQL EXPERIMENTS — Forced Algorithms & Forced Order")
    print("=" * 110)

    # Increase work_mem so hash joins don't spill to disk
    base_settings = ["SET work_mem = '256MB'"]

    con = psycopg.connect(PG_CONNSTR, autocommit=True)

    results = []

    # ── Experiment A: Forced JOIN algorithms on 2-table join ──
    print("\n── A. Forced algorithms (masterfile ⟕ lung_cancer) ──")
    print(f"  {'Label':40s} | {'Algorithm':20s} | {'Time':>20s} | {'Cardinality':>30s} | Engine")

    for algo_label, settings in [
        ("PG-A1-hash",      base_settings + ["SET enable_hashjoin=on",  "SET enable_mergejoin=off", "SET enable_nestloop=off"]),
        ("PG-A2-merge",     base_settings + ["SET enable_hashjoin=off", "SET enable_mergejoin=on",  "SET enable_nestloop=off"]),
        ("PG-A3-nestloop",  base_settings + ["SET enable_hashjoin=off", "SET enable_mergejoin=off", "SET enable_nestloop=on"]),
        ("PG-A4-optimizer", base_settings + ["SET enable_hashjoin=on",  "SET enable_mergejoin=on",  "SET enable_nestloop=on"]),
    ]:
        results.append(run_query(con, Q_2TABLE, algo_label, settings))

    # ── Experiment B: Forced algorithms on 3-table join ──
    print("\n── B. Forced algorithms (path ⟕ mf ⟕ lc) ──")
    for algo_label, settings in [
        ("PG-B1-hash",      base_settings + ["SET enable_hashjoin=on",  "SET enable_mergejoin=off", "SET enable_nestloop=off"]),
        ("PG-B2-merge",     base_settings + ["SET enable_hashjoin=off", "SET enable_mergejoin=on",  "SET enable_nestloop=off"]),
        ("PG-B3-nestloop",  base_settings + ["SET enable_hashjoin=off", "SET enable_mergejoin=off", "SET enable_nestloop=on"]),
        ("PG-B4-optimizer", base_settings + ["SET enable_hashjoin=on",  "SET enable_mergejoin=on",  "SET enable_nestloop=on"]),
    ]:
        results.append(run_query(con, Q_3TABLE, algo_label, settings))

    # ── Experiment C: Forced JOIN order (3 tables) ──
    print("\n── C. Forced order (3 tables) ──")
    order_settings = base_settings + [
        "SET enable_hashjoin=on", "SET enable_mergejoin=on", "SET enable_nestloop=on"
    ]
    for label, sql, extra in [
        ("PG-C1-natural-optimized",  Q_3TABLE,     order_settings + ["SET join_collapse_limit=8"]),
        ("PG-C2-natural-forced",     Q_3TABLE,     order_settings + ["SET join_collapse_limit=1"]),
        ("PG-C3-reversed-forced",    Q_3TABLE_REV, order_settings + ["SET join_collapse_limit=1"]),
    ]:
        results.append(run_query(con, sql, label, extra))

    # ── Experiment D: Forced JOIN order (4 tables) ──
    print("\n── D. Forced order (4 tables) ──")
    for label, sql, extra in [
        ("PG-D1-natural-optimized",  Q_4TABLE,     order_settings + ["SET join_collapse_limit=8"]),
        ("PG-D2-natural-forced",     Q_4TABLE,     order_settings + ["SET join_collapse_limit=1"]),
        ("PG-D3-reversed-forced",    Q_4TABLE_REV, order_settings + ["SET join_collapse_limit=1"]),
    ]:
        results.append(run_query(con, sql, label, extra))

    con.close()

    # Save results
    with open(RESULTS_DIR / "pg_experiment_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_DIR / 'pg_experiment_results.json'}")
    print(f"Plans saved to {PLANS_DIR}/")
    print("\n✓ Done!")


if __name__ == "__main__":
    main()