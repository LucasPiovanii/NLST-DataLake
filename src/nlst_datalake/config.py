"""Paths e constantes do Data Lake NLST."""

from pathlib import Path

# ── Raiz do projeto ───────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ── Data Lake ─────────────────────────────────────────────────
DATALAKE_ROOT = PROJECT_ROOT / "datalake"

BRONZE_ROOT = DATALAKE_ROOT / "bronze"
SILVER_ROOT = DATALAKE_ROOT / "silver"
GOLD_ROOT   = DATALAKE_ROOT / "gold"

# ── Bronze: Lung Cancer (DICOM) ──────────────────────────────
LUNG_CANCER_ROOT = BRONZE_ROOT / "lung_cancer_samples"

LUNG_CANCER_SOURCES = {
    "screen_detected": LUNG_CANCER_ROOT / "screen_detected",
    "other":           LUNG_CANCER_ROOT / "other",
}

# ── Silver ────────────────────────────────────────────────────
SILVER_LUNG_CANCER = SILVER_ROOT / "lung_cancer_metadata.parquet"
# Nota: pathology Silver é gerenciado por nlst_pathology.config

# ── Gold ──────────────────────────────────────────────────────
GOLD_PATHOLOGY   = GOLD_ROOT / "pathology.parquet"
GOLD_LUNG_CANCER = GOLD_ROOT / "lung_cancer.parquet"

# ── DuckDB ────────────────────────────────────────────────────
DUCKDB_PATH = DATALAKE_ROOT / "nlst.duckdb"

# ── Experimentos ──────────────────────────────────────────────
EXPERIMENTS_ROOT = PROJECT_ROOT / "experiments"
QUERIES_DIR      = EXPERIMENTS_ROOT / "queries"
PLANS_DIR        = EXPERIMENTS_ROOT / "plans"
RESULTS_DIR      = EXPERIMENTS_ROOT / "results"