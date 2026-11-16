#!/usr/bin/env python3
"""Load Gold Parquets into PostgreSQL and generate statistics."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import duckdb

GOLD = PROJECT_ROOT / "datalake" / "gold"
PG_CONNSTR = "dbname=nlst port=5433 host=/tmp"

TABLES = [
    "pathology", "masterfile", "lung_cancer", "participant",
    "cause_of_death", "medical_complications", "treatment",
]


def main():
    print("=" * 60)
    print("SETUP POSTGRESQL — Load Gold Tables via DuckDB")
    print("=" * 60)

    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute(f"ATTACH 'dbname=nlst port=5433 host=/tmp' AS pg (TYPE postgres)")

    for t in TABLES:
        parquet = GOLD / f"{t}.parquet"
        print(f"\n  Loading {t}...")
        con.execute(f"DROP TABLE IF EXISTS pg.{t}")
        con.execute(f"CREATE TABLE pg.{t} AS SELECT * FROM read_parquet('{parquet}')")
        count = con.execute(f"SELECT COUNT(*) FROM pg.{t}").fetchone()[0]
        print(f"    {count:,} rows ✓")

    # ANALYZE via psycopg (DuckDB's postgres extension can't run ANALYZE)
    con.close()

    import psycopg
    with psycopg.connect(PG_CONNSTR) as pgcon:
        pgcon.autocommit = True
        for t in TABLES:
            pgcon.execute(f"ANALYZE {t}")
            print(f"  ANALYZE {t} ✓")

        # Validate JOINs
        print("\n── JOIN validation ──")
        joins = [
            ("pathology ⟕ masterfile",
             "SELECT COUNT(*) FROM pathology p JOIN masterfile m ON p.slide_id = m.slide_id"),
            ("masterfile ⟕ lung_cancer",
             "SELECT COUNT(*) FROM masterfile m JOIN lung_cancer lc ON m.patient_id = lc.patient_id"),
            ("3-way: path ⟕ mf ⟕ lc",
             "SELECT COUNT(*) FROM pathology p JOIN masterfile m ON p.slide_id = m.slide_id "
             "JOIN lung_cancer lc ON m.patient_id = lc.patient_id"),
        ]
        for label, sql in joins:
            row = pgcon.execute(sql).fetchone()
            print(f"  {label:40s} → {row[0]:>10,} rows")

        # Show config
        print("\n── PostgreSQL config ──")
        for param in ["work_mem", "shared_buffers", "max_parallel_workers_per_gather",
                       "effective_cache_size", "random_page_cost"]:
            val = pgcon.execute(f"SHOW {param}").fetchone()[0]
            print(f"  {param}: {val}")

    print("\n✓ Done!")


if __name__ == "__main__":
    main()