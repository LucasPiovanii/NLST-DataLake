#!/usr/bin/env python3
"""Build Gold participant table from Silver: prefer labels over codes, keep all relevant columns."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import polars as pl

SILVER = PROJECT_ROOT / "datalake" / "silver"
GOLD = PROJECT_ROOT / "datalake" / "gold"


def main() -> None:
    print("=" * 60)
    print("BUILD GOLD — Participant")
    print("=" * 60)

    GOLD.mkdir(parents=True, exist_ok=True)

    df = pl.read_parquet(SILVER / "participant.parquet")
    print(f"\nSilver: {df.shape[0]} rows × {df.shape[1]} cols")

    all_cols = set(df.columns)
    label_cols = {c for c in all_cols if c.endswith("_label")}
    base_cols_with_label = {c.replace("_label", "") for c in label_cols}

    # Strategy:
    # - If a column has a _label version → keep only the _label, renamed without suffix
    # - If a column has NO _label version → keep the original
    # - Skip dataset_version (not useful)
    # - Rename pid → patient_id

    skip = {"dataset_version"}

    select_exprs = []
    final_names = set()

    # First: pid → patient_id
    select_exprs.append(pl.col("pid").cast(pl.Utf8).alias("patient_id"))
    final_names.add("pid")

    # Process all original (non-label) columns
    for col in df.columns:
        if col in skip or col in final_names:
            continue
        if col.endswith("_label"):
            continue  # handled below with the base column

        label_version = f"{col}_label"

        if label_version in label_cols:
            # Has label → use label, rename to original name
            select_exprs.append(pl.col(label_version).alias(col))
        else:
            # No label → keep original
            select_exprs.append(pl.col(col))

        final_names.add(col)

    gold = df.select(select_exprs)

    # Save
    output_path = GOLD / "participant.parquet"
    gold.write_parquet(output_path)

    print(f"\nGold: {gold.shape[0]} rows × {gold.shape[1]} cols")
    print(f"Saved to {output_path}")

    # Stats
    labeled = len(base_cols_with_label & final_names)
    unlabeled = gold.shape[1] - labeled - 1  # -1 for patient_id
    print(f"\n  Columns with labels applied: {labeled}")
    print(f"  Columns kept as-is (numeric/no mapping): {unlabeled}")

    # Sample
    sample_cols = ["patient_id", "gender", "race", "age", "cigsmok", "lung_cancer", "de_type"]
    available = [c for c in sample_cols if c in gold.columns]
    print(f"\n  Sample:")
    print(gold.select(available).head(5))

    print("\n✓ Done!")


if __name__ == "__main__":
    main()