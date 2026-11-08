#!/usr/bin/env python3
"""Build Gold treatment: labels, drop codes, rename pid."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import polars as pl

SILVER = PROJECT_ROOT / "datalake" / "silver"
GOLD = PROJECT_ROOT / "datalake" / "gold"


def main() -> None:
    print("=" * 60)
    print("BUILD GOLD — Treatment")
    print("=" * 60)

    GOLD.mkdir(parents=True, exist_ok=True)

    df = pl.read_parquet(SILVER / "treatment.parquet")
    print(f"\nSilver: {df.shape[0]} rows × {df.shape[1]} cols")

    gold = df.select([
        pl.col("pid").cast(pl.Utf8).alias("patient_id"),
        pl.col("treat_label").alias("treatment_category"),
        pl.col("treatnum_label").alias("treatment_procedure"),
        pl.col("treat_days"),
        pl.col("treat_year_label").alias("treatment_year"),
        pl.col("disease_post_surg_label").alias("residual_disease"),
        pl.col("rad_stop_days"),
    ])

    output_path = GOLD / "treatment.parquet"
    gold.write_parquet(output_path)

    print(f"Gold: {gold.shape[0]} rows × {gold.shape[1]} cols")
    print(f"Saved to {output_path}")
    print(f"\nSample:")
    print(gold.head(5))
    print("\n✓ Done!")


if __name__ == "__main__":
    main()