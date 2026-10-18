"""
Configuration for the NLST Lung Cancer library.

Paths point to the Bronze layer of the local Data Lake.
"""

from pathlib import Path

# =============================================================================
# Project Paths
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# =============================================================================
# Data Lake Paths
# =============================================================================

DATALAKE_ROOT = PROJECT_ROOT / "datalake"

BRONZE_ROOT = DATALAKE_ROOT / "bronze"
SILVER_ROOT = DATALAKE_ROOT / "silver"

# ── Bronze: Lung Cancer ──────────────────────────────────────
LUNG_CANCER_ROOT = BRONZE_ROOT / "lung_cancer_samples"

LUNG_CANCER_SOURCES = {
    "screen_detected": LUNG_CANCER_ROOT / "screen_detected",
    "other":           LUNG_CANCER_ROOT / "other",
}

# ── Silver: Output ───────────────────────────────────────────
SILVER_LUNG_CANCER_CATALOG = SILVER_ROOT / "lung_cancer_metadata.parquet"