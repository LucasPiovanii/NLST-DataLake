#!/usr/bin/env python3
"""
Setup DuckDB: load Gold Parquets as native tables and generate optimizer statistics.

This script creates the DuckDB database that will be used for all JOIN experiments.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import duckdb

GOLD = PROJECT_ROOT / "datalake" / "gold"
DUCKDB_PATH = PROJECT_ROOT / "datalake" / "nlst.duckdb"


def main() -> None:
    print("=" * 60)
    print("SETUP DUCKDB — Load Gold Tables")
    print("=" * 60)

    # Se já existe, remove para recriar do zero
    if DUCKDB_PATH.exists():
        DUCKDB_PATH.unlink()
        print(f"\nRemoved existing database: {DUCKDB_PATH}")

    # Conectar (cria o arquivo)
    con = duckdb.connect(str(DUCKDB_PATH))
    print(f"Connected to: {DUCKDB_PATH}")

    # ── 1. Criar tabelas a partir dos Parquets Gold ──────────
    print("\n── 1. Criando tabelas ──")

    tables = {
        "pathology": GOLD / "pathology.parquet",
        "masterfile": GOLD / "masterfile.parquet",
        "lung_cancer": GOLD / "lung_cancer.parquet",
    }

    for table_name, parquet_path in tables.items():
        con.sql(f"""
            CREATE TABLE {table_name} AS 
            SELECT * FROM read_parquet('{parquet_path}')
        """)

        count = con.sql(f"SELECT COUNT(*) AS n FROM {table_name}").fetchone()[0]
        cols = len(con.sql(f"DESCRIBE {table_name}").fetchall())
        print(f"  {table_name}: {count:,} rows × {cols} cols ✓")

    # ── 2. Gerar estatísticas para o otimizador ──────────────
    print("\n── 2. Gerando estatísticas (ANALYZE) ──")

    for table_name in tables:
        con.sql(f"ANALYZE {table_name}")
        print(f"  ANALYZE {table_name} ✓")

    # ── 3. Verificar o catálogo ──────────────────────────────
    print("\n── 3. Catálogo de tabelas ──")

    result = con.sql("SHOW TABLES").fetchall()
    for row in result:
        print(f"  - {row[0]}")

    # ── 4. Schemas das tabelas ───────────────────────────────
    print("\n── 4. Schemas ──")

    for table_name in tables:
        print(f"\n  {table_name}:")
        schema = con.sql(f"DESCRIBE {table_name}").fetchall()
        for col_name, col_type, *_ in schema:
            print(f"    {col_name}: {col_type}")

    # ── 5. Preview dos dados ─────────────────────────────────
    print("\n── 5. Preview ──")

    for table_name in tables:
        print(f"\n  {table_name} (primeiras 3 linhas):")
        con.sql(f"SELECT * FROM {table_name} LIMIT 3").show()

    # ── 6. Validação rápida dos JOINs ────────────────────────
    print("\n── 6. Validação dos JOINs ──")

    # Q1: pathology ↔ masterfile
    q1 = con.sql("""
        SELECT COUNT(*) AS n
        FROM pathology p
        JOIN masterfile m ON p.slide_id = m.slide_id
    """).fetchone()[0]
    print(f"  pathology ⟕ masterfile:          {q1:,} rows")

    # Q2: masterfile ↔ lung_cancer
    q2 = con.sql("""
        SELECT COUNT(*) AS n
        FROM masterfile m
        JOIN lung_cancer lc ON m.patient_id = lc.patient_id
    """).fetchone()[0]
    print(f"  masterfile ⟕ lung_cancer:        {q2:,} rows")

    # Q3: 3-way join
    q3 = con.sql("""
        SELECT COUNT(*) AS n
        FROM pathology p
        JOIN masterfile m ON p.slide_id = m.slide_id
        JOIN lung_cancer lc ON m.patient_id = lc.patient_id
    """).fetchone()[0]
    print(f"  pathology ⟕ masterfile ⟕ lc:     {q3:,} rows")

    # ── 7. Testar EXPLAIN ────────────────────────────────────
    print("\n── 7. Teste EXPLAIN (plano estimado) ──")

    plan = con.sql("""
        EXPLAIN
        SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality
        FROM pathology p
        JOIN masterfile m ON p.slide_id = m.slide_id
        JOIN lung_cancer lc ON m.patient_id = lc.patient_id
    """).fetchall()

    for row in plan:
        print(row[1])

    # ── 8. Testar EXPLAIN ANALYZE ────────────────────────────
    print("\n── 8. Teste EXPLAIN ANALYZE (plano real) ──")

    plan_analyze = con.sql("""
        EXPLAIN ANALYZE
        SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality
        FROM pathology p
        JOIN masterfile m ON p.slide_id = m.slide_id
        JOIN lung_cancer lc ON m.patient_id = lc.patient_id
    """).fetchall()

    for row in plan_analyze:
        print(row[1])

    # ── Resumo ───────────────────────────────────────────────
    db_size = DUCKDB_PATH.stat().st_size / (1024**2)

    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"  Database: {DUCKDB_PATH}")
    print(f"  Size: {db_size:.1f} MB")
    print(f"  Tables: {len(tables)}")
    print(f"  JOINs validados: todos funcionando ✓")
    print("\n✓ Done!")

    con.close()


if __name__ == "__main__":
    main()