#!/usr/bin/env python3
"""Build Silver medical_complications (CSV + SAS Formats → Parquet)."""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd
import polars as pl

BRONZE = PROJECT_ROOT / "datalake" / "bronze" / "dictionaries" / "medical_complications"
SILVER = PROJECT_ROOT / "datalake" / "silver"

CSV_PATH = BRONZE / "medical_complications_d040722.csv"
SAS_PATH = BRONZE / "medical_complications.sas_formats.d040722.sas"
OUTPUT_PATH = SILVER / "medical_complications.parquet"


def parse_sas_formats(sas_path: Path) -> dict[str, dict]:
    content = sas_path.read_text(encoding="latin-1")
    formats = {}
    current_variable = None
    current_mappings = {}

    for line in content.splitlines():
        line = line.strip()

        var_match = re.match(r"\*\* FOR VARIABLE:\s+(.+?)\s+\*\*;", line)
        if var_match:
            current_variable = var_match.group(1)
            current_mappings = {}
            continue

        mapping_match = re.match(r'^\s*("?[^"=]+?"?)\s*=\s*"(.+?)"\s*$', line)
        if mapping_match and current_variable:
            raw_key = mapping_match.group(1).strip().strip('"')
            label = mapping_match.group(2).strip()
            current_mappings[raw_key] = label
            continue

        if line == ";" and current_variable and current_mappings:
            formats[current_variable] = current_mappings
            current_variable = None
            current_mappings = {}

    return formats


def apply_sas_formats(df: pd.DataFrame, formats: dict[str, dict]) -> pd.DataFrame:
    df = df.copy()
    applied = 0

    for variable, mappings in formats.items():
        if variable not in df.columns or not mappings:
            continue

        label_col = f"{variable}_label"
        str_mappings = {}
        for k, v in mappings.items():
            str_mappings[str(k)] = v
            try:
                str_mappings[str(int(float(k)))] = v
            except (ValueError, TypeError):
                pass

        df[label_col] = df[variable].astype(str).map(str_mappings)
        applied += 1

    print(f"  Applied SAS formats to {applied} columns")
    return df


def main() -> None:
    print("=" * 60)
    print("BUILD SILVER — Medical Complications (CSV + SAS → Parquet)")
    print("=" * 60)

    SILVER.mkdir(parents=True, exist_ok=True)

    print(f"\n── 1. Reading CSV ──")
    df = pd.read_csv(CSV_PATH, low_memory=False)
    print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} cols")

    print(f"\n── 2. Parsing SAS formats ──")
    formats = parse_sas_formats(SAS_PATH)
    print(f"  Found mappings for {len(formats)} variables")
    for var, mappings in formats.items():
        print(f"    {var}: {len(mappings)} values")

    print(f"\n── 3. Applying SAS formats ──")
    df = apply_sas_formats(df, formats)
    print(f"  New shape: {df.shape[0]} rows × {df.shape[1]} cols")

    print(f"\n── 4. Saving to Silver ──")
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).replace("nan", None)

    df_pl = pl.from_pandas(df)
    df_pl.write_parquet(OUTPUT_PATH)
    print(f"  Saved to {OUTPUT_PATH}")
    print(f"  Rows: {df_pl.shape[0]}, Columns: {df_pl.shape[1]}")

    print(f"\n── 5. Validation ──")
    df_check = pl.read_parquet(OUTPUT_PATH)
    print(df_check.head(5))

    print("\n✓ Done!")


if __name__ == "__main__":
    main()