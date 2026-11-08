#!/usr/bin/env python3
"""Build Gold medical_complications: labels, drop codes, rename pid."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import polars as pl

SILVER = PROJECT_ROOT / "datalake" / "silver"
GOLD = PROJECT_ROOT / "datalake" / "gold"


def main() -> None:
    print("=" * 60)
    print("BUILD GOLD — Medical Complications")
    print("=" * 60)

    GOLD.mkdir(parents=True, exist_ok=True)

    df = pl.read_parquet(SILVER / "medical_complications.parquet")
    print(f"\nSilver: {df.shape[0]} rows × {df.shape[1]} cols")

    gold = df.select([
        pl.col("pid").cast(pl.Utf8).alias("patient_id"),
        pl.col("comp_days"),
        pl.col("comp_year_label").alias("comp_year"),
        pl.col("compcat_label").alias("complication_category"),
        pl.col("compcode_label").alias("complication_code"),
        pl.col("can_link_label").alias("cancer_linked"),
        pl.col("scr_link_label").alias("screening_linked"),
    ])

    output_path = GOLD / "medical_complications.parquet"
    gold.write_parquet(output_path)

    print(f"Gold: {gold.shape[0]} rows × {gold.shape[1]} cols")
    print(f"Saved to {output_path}")
    print(f"\nSample:")
    print(gold.head(5))
    print("\n✓ Done!")


if __name__ == "__main__":
    main()