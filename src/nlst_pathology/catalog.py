"""
Build the pathology metadata catalog and save to the Silver layer.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from .config import SILVER_PATHOLOGY_CATALOG, ensure_output_directories
from .discovery import BatchInfo, list_slides
from .slide import open_slide, close_slide


def build_metadata_catalog(
    batches: list[BatchInfo],
) -> pl.DataFrame:
    """
    Build a metadata catalog for one or more pathology batches.

    Parameters
    ----------
    batches
        List of pathology batches.

    Returns
    -------
    polars.DataFrame
        One row per slide.
    """
    records = []

    for batch in batches:
        slides = list_slides(batch)

        for slide_path in slides:
            slide = open_slide(slide_path)
            file_size_bytes = slide_path.stat().st_size

            record = {
                # Batch information
                "batch": batch.name,
                "cancer_type": batch.cancer_type,

                # File information
                "filename": slide_path.name,
                "slide_id": slide_path.stem,
                "path": str(slide_path),
                "file_size_bytes": file_size_bytes,
                "file_size_mb": round(file_size_bytes / (1024**2), 2),
                "file_size_gb": round(file_size_bytes / (1024**3), 4),

                # Image information
                "width": slide.dimensions[0],
                "height": slide.dimensions[1],
                "level_count": slide.level_count,
            }

            # Add every OpenSlide property
            record.update(dict(slide.properties))

            records.append(record)
            close_slide(slide)

    return pl.DataFrame(records)


def save_catalog_to_silver(
    catalog: pl.DataFrame,
    output_path: Path = SILVER_PATHOLOGY_CATALOG,
) -> Path:
    """
    Save the pathology catalog as Parquet in the Silver layer.

    Parameters
    ----------
    catalog
        Pathology metadata catalog.
    output_path
        Destination Parquet file.

    Returns
    -------
    Path
        Path to the saved Parquet file.
    """
    ensure_output_directories()
    catalog.write_parquet(output_path)
    print(f"Catalog saved to {output_path}")
    print(f"  Rows: {catalog.shape[0]}")
    print(f"  Columns: {catalog.shape[1]}")
    return output_path
