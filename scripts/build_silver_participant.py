#!/usr/bin/env python3
"""
Build Silver layer for participant data (Bronze CSV → Silver Parquet).

Reads the participant CSV and the SAS formats file, parses the value
mappings from the SAS PROC FORMAT, and applies them to create labeled
columns alongside the original coded columns. All 356 columns are kept.

For each coded column that has a SAS format mapping, a new column
`<original_name>_label` is added with the human-readable label.
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd
import polars as pl

BRONZE = PROJECT_ROOT / "datalake" / "bronze" / "dictionaries" / "participant_dictionary"
SILVER = PROJECT_ROOT / "datalake" / "silver"

CSV_PATH = BRONZE / "participant_d040722.csv"
SAS_PATH = BRONZE / "participant.sas_formats.d040722.sas"
OUTPUT_PATH = SILVER / "participant.parquet"


# ─────────────────────────────────────────────────────────────
# SAS Format Parser
# ─────────────────────────────────────────────────────────────


def parse_sas_formats(sas_path: Path) -> dict[str, dict]:
    """
    Parse a SAS PROC FORMAT file and return a dict of variable → {code: label}.

    The SAS file has blocks like:

        ** FORMAT: genderf **;
        ** FOR VARIABLE: gender **;
        value genderf
          1 = "Male"
          2 = "Female"
        ;

    For character formats (prefixed with $), the keys are strings.
    For numeric formats, the keys are numbers (int or float).
    Entries like `.M = "Missing"` or `.N = "Not applicable"` use
    special SAS missing codes — we store them as strings ".M", ".N".

    Returns
    -------
    dict[str, dict]
        Mapping from variable name to {code: label}.
        Only variables with at least one mapping are included.
    """
    content = sas_path.read_text(encoding="latin-1")

    formats = {}
    current_variable = None
    current_mappings = {}
    is_character = False

    for line in content.splitlines():
        line = line.strip()

        # Detect variable name
        var_match = re.match(r"\*\* FOR VARIABLE:\s+(.+?)\s+\*\*;", line)
        if var_match:
            current_variable = var_match.group(1)
            current_mappings = {}
            continue

        # Detect if character variable
        if "CHARACTER VARIABLE" in line:
            is_character = True
            continue

        # Detect if continuous numeric (no mappings expected)
        if "CONTINUOUS NUMERIC VARIABLE" in line:
            is_character = False
            continue

        # Parse value mappings: handles patterns like:
        #   1 = "Male"
        #   .M = "Missing"
        #   .N = "Not ineligible"
        #   "EV" = "Underlying cause..."
        mapping_match = re.match(
            r'^\s*("?[^"=]+?"?)\s*=\s*"(.+?)"\s*$', line
        )
        if mapping_match and current_variable:
            raw_key = mapping_match.group(1).strip().strip('"')
            label = mapping_match.group(2).strip()
            current_mappings[raw_key] = label
            continue

        # End of a value block
        if line == ";" and current_variable and current_mappings:
            formats[current_variable] = current_mappings
            current_variable = None
            current_mappings = {}
            is_character = False

    return formats


def apply_sas_formats(
    df: pd.DataFrame,
    formats: dict[str, dict],
) -> pd.DataFrame:
    """
    For each column in df that has a SAS format mapping, add a
    `<column>_label` column with the human-readable labels.

    The original column is preserved unchanged.
    """
    df = df.copy()

    applied = 0

    for variable, mappings in formats.items():
        if variable not in df.columns:
            continue

        if not mappings:
            continue

        label_col = f"{variable}_label"

        # Build a mapping that handles both numeric and string keys
        str_mappings = {}
        for k, v in mappings.items():
            str_mappings[str(k)] = v
            # Also try numeric conversion for matching
            try:
                str_mappings[str(int(float(k)))] = v
            except (ValueError, TypeError):
                pass

        # Convert column values to string for matching, then map
        df[label_col] = (
            df[variable]
            .astype(str)
            .map(str_mappings)
        )

        applied += 1

    print(f"  Applied SAS formats to {applied} columns")
    return df


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────


def main() -> None:
    print("=" * 60)
    print("BUILD SILVER — Participant (CSV + SAS Formats → Parquet)")
    print("=" * 60)

    SILVER.mkdir(parents=True, exist_ok=True)

    # 1. Read CSV
    print(f"\n── 1. Reading CSV ──")
    print(f"  Source: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, low_memory=False)
    print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} cols")

    # 2. Parse SAS formats
    print(f"\n── 2. Parsing SAS formats ──")
    print(f"  Source: {SAS_PATH}")
    formats = parse_sas_formats(SAS_PATH)
    print(f"  Found mappings for {len(formats)} variables")

    # Show a few examples
    for var in list(formats.keys())[:5]:
        n_vals = len(formats[var])
        sample = list(formats[var].items())[:3]
        print(f"    {var}: {n_vals} values — e.g. {sample}")

    # 3. Apply SAS formats (add _label columns)
    print(f"\n── 3. Applying SAS formats ──")
    df = apply_sas_formats(df, formats)
    print(f"  New shape: {df.shape[0]} rows × {df.shape[1]} cols")

    # 4. Convert to Polars and save as Parquet
    print(f"\n── 4. Saving to Silver ──")

    # Normalize mixed-type columns to string before Polars conversion
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).replace("nan", None)

    df_pl = pl.from_pandas(df)
    df_pl.write_parquet(OUTPUT_PATH)

    print(f"  Saved to {OUTPUT_PATH}")
    print(f"  Rows: {df_pl.shape[0]}")
    print(f"  Columns: {df_pl.shape[1]}")

    # 5. Validate
    print(f"\n── 5. Validation ──")
    df_check = pl.read_parquet(OUTPUT_PATH)
    print(f"  Read back: {df_check.shape[0]} rows × {df_check.shape[1]} cols")

    # Show some label columns
    label_cols = [c for c in df_check.columns if c.endswith("_label")]
    print(f"  Label columns created: {len(label_cols)}")
    if label_cols:
        print(f"  Examples: {label_cols[:10]}")

        # Show a sample
        sample_cols = ["pid", "gender", "gender_label", "race", "race_label",
                       "cigsmok", "cigsmok_label"]
        available = [c for c in sample_cols if c in df_check.columns]
        print(f"\n  Sample data:")
        print(df_check.select(available).head(5))

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
