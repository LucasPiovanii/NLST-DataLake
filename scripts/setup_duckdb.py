#!/usr/bin/env python3
"""Setup DuckDB: load all 7 Gold Parquets as native tables and generate optimizer statistics."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import duckdb

GOLD = PROJECT_ROOT / "datalake" / "gold"
DUCKDB_PATH = PROJECT_ROOT / "datalake" / "nlst.duckdb"

TABLES = {
    "pathology":              GOLD / "pathology.parquet",
    "masterfile":             GOLD / "masterfile.parquet",
    "lung_cancer":            GOLD / "lung_cancer.parquet",
    "participant":            GOLD / "participant.parquet",
    "cause_of_death":         GOLD / "cause_of_death.parquet",
    "medical_complications":  GOLD / "medical_complications.parquet",
    "treatment":              GOLD / "treatment.parquet",
}


def main() -> None:
    print("=" * 60)
    print("SETUP DUCKDB — Load All Gold Tables")
    print("=" * 60)

    # Recreate from scratch
    if DUCKDB_PATH.exists():
        DUCKDB_PATH.unlink()
        print(f"\nRemoved existing database")

    con = duckdb.connect(str(DUCKDB_PATH))
    print(f"Connected to: {DUCKDB_PATH}")

    # ── 1. Create tables ─────────────────────────────────────
    print("\n── 1. Creating tables ──")
    for name, path in TABLES.items():
        con.sql(f"CREATE TABLE {name} AS SELECT * FROM read_parquet('{path}')")
        count = con.sql(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        cols = len(con.sql(f"DESCRIBE {name}").fetchall())
        print(f"  {name:30s} {count:>10,} rows × {cols:>3} cols ✓")

    # ── 2. Generate statistics ────────────────────────────────
    print("\n── 2. ANALYZE ──")
    for name in TABLES:
        con.sql(f"ANALYZE {name}")
        print(f"  ANALYZE {name} ✓")

    # ── 3. Catalog ────────────────────────────────────────────
    print("\n── 3. Tables in catalog ──")
    for row in con.sql("SHOW TABLES").fetchall():
        print(f"  - {row[0]}")

    # ── 4. Validate JOINs ────────────────────────────────────
    print("\n── 4. JOIN validation ──")

    joins = [
        ("pathology ⟕ masterfile",
         "SELECT COUNT(*) FROM pathology p JOIN masterfile m ON p.slide_id = m.slide_id"),
        ("masterfile ⟕ lung_cancer",
         "SELECT COUNT(*) FROM masterfile m JOIN lung_cancer lc ON m.patient_id = lc.patient_id"),
        ("masterfile ⟕ participant",
         "SELECT COUNT(*) FROM masterfile m JOIN participant pt ON m.patient_id = pt.patient_id"),
        ("participant ⟕ treatment",
         "SELECT COUNT(*) FROM participant pt JOIN treatment t ON pt.patient_id = t.patient_id"),
        ("participant ⟕ cause_of_death",
         "SELECT COUNT(*) FROM participant pt JOIN cause_of_death cod ON pt.patient_id = cod.patient_id"),
        ("participant ⟕ medical_complications",
         "SELECT COUNT(*) FROM participant pt JOIN medical_complications mc ON pt.patient_id = mc.patient_id"),
        ("3-way: path ⟕ mf ⟕ lc",
         "SELECT COUNT(*) FROM pathology p JOIN masterfile m ON p.slide_id = m.slide_id JOIN lung_cancer lc ON m.patient_id = lc.patient_id"),
        ("3-way: mf ⟕ participant ⟕ treatment",
         "SELECT COUNT(*) FROM masterfile m JOIN participant pt ON m.patient_id = pt.patient_id JOIN treatment t ON pt.patient_id = t.patient_id"),
        ("4-way: path ⟕ mf ⟕ lc ⟕ treatment",
         "SELECT COUNT(*) FROM pathology p JOIN masterfile m ON p.slide_id = m.slide_id JOIN lung_cancer lc ON m.patient_id = lc.patient_id JOIN treatment t ON m.patient_id = t.patient_id"),
    ]

    for label, sql in joins:
        try:
            count = con.sql(sql).fetchone()[0]
            print(f"  {label:45s} → {count:>10,} rows")
        except Exception as e:
            print(f"  {label:45s} → ERROR: {e}")

    # ── 5. EXPLAIN ANALYZE test ──────────────────────────────
    print("\n── 5. EXPLAIN ANALYZE (4-way join) ──")
    plan = con.sql("""
        EXPLAIN ANALYZE
        SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality, t.treatment_category
        FROM pathology p
        JOIN masterfile m ON p.slide_id = m.slide_id
        JOIN lung_cancer lc ON m.patient_id = lc.patient_id
        JOIN treatment t ON m.patient_id = t.patient_id
    """).fetchall()
    for row in plan:
        print(row[1])

    # ── Summary ──────────────────────────────────────────────
    db_size = DUCKDB_PATH.stat().st_size / (1024**2)
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Database: {DUCKDB_PATH}")
    print(f"  Size: {db_size:.1f} MB")
    print(f"  Tables: {len(TABLES)}")
    print("\n✓ Done!")

    con.close()


if __name__ == "__main__":
    main()