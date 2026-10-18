#!/usr/bin/env python3
"""Convert the pathology masterfile from SAS to Parquet (Bronze → Silver)."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd
import polars as pl

BRONZE = PROJECT_ROOT / "datalake" / "bronze"
SILVER = PROJECT_ROOT / "datalake" / "silver"


def main() -> None:
    print("=" * 60)
    print("BUILD SILVER — Masterfile (SAS → Parquet)")
    print("=" * 60)

    SILVER.mkdir(parents=True, exist_ok=True)

    # Ler SAS com pandas (único formato que lê .sas7bdat nativamente)
    sas_path = BRONZE / "dictionaries" / "pathology_images_d040722.sas7bdat"
    print(f"\nSource: {sas_path}")

    df_pd = pd.read_sas(sas_path, encoding="latin-1")
    print(f"Rows: {len(df_pd)}, Columns: {len(df_pd.columns)}")

    # Converter para Polars e salvar como Parquet
    df = pl.from_pandas(df_pd)

    output_path = SILVER / "masterfile.parquet"
    df.write_parquet(output_path)

    print(f"\nSaved to {output_path}")
    print(f"  Rows: {df.shape[0]}")
    print(f"  Columns: {df.shape[1]}")

    # Validar
    df_check = pl.read_parquet(output_path)
    print(f"\nValidação: {df_check.shape[0]} rows × {df_check.shape[1]} cols")

    print("\n✓ Done!")


if __name__ == "__main__":
    main()