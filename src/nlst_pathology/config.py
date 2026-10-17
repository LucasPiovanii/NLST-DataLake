"""
Configuration for the NLST Pathology library.

Paths point to the Bronze layer of the local Data Lake.
"""

from pathlib import Path

# =============================================================================
# Project Paths
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SRC_ROOT = PROJECT_ROOT / "src"
NOTEBOOKS_ROOT = PROJECT_ROOT / "notebooks"

# =============================================================================
# Data Lake Paths
# =============================================================================

DATALAKE_ROOT = PROJECT_ROOT / "datalake"

BRONZE_ROOT = DATALAKE_ROOT / "bronze"
SILVER_ROOT = DATALAKE_ROOT / "silver"
GOLD_ROOT = DATALAKE_ROOT / "gold"

# ── Bronze: Patologia ────────────────────────────────────────
PATHOLOGY_ROOT = BRONZE_ROOT / "pathology_samples"

# ── Silver: Outputs ──────────────────────────────────────────
SILVER_PATHOLOGY_CATALOG = SILVER_ROOT / "pathology_metadata.parquet"

# =============================================================================
# Image Parameters
# =============================================================================

THUMBNAIL_SIZE = (512, 512)

SUPPORTED_SLIDE_EXTENSIONS = {".svs"}

# =============================================================================
# OpenSlide Metadata Keys
# =============================================================================

OPENSLIDE_KEYS = [
    "openslide.vendor",
    "openslide.level-count",
    "openslide.objective-power",
    "openslide.quickhash-1",
    "openslide.comment",
]

# =============================================================================
# Aperio Metadata Keys
# =============================================================================

APERIO_KEYS = [
    "aperio.AppMag",
    "aperio.Date",
    "aperio.Filename",
    "aperio.MPP",
    "aperio.ScanScope ID",
]

# =============================================================================
# Utility
# =============================================================================

def ensure_output_directories() -> None:
    """Create Silver and Gold directories if they do not exist."""
    SILVER_ROOT.mkdir(parents=True, exist_ok=True)
    GOLD_ROOT.mkdir(parents=True, exist_ok=True)
