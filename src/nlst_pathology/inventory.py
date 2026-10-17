"""
Inventory utilities for NLST pathology batches.

This module is responsible for inspecting the filesystem and
building an inventory of pathology slides.

It does NOT inspect slide metadata or image contents.
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .discovery import BatchInfo
from .discovery import list_slides


# =============================================================================
# Dataclasses
# =============================================================================


@dataclass(frozen=True)
class SlideInventory:
    """
    Filesystem information for a single pathology slide.
    """

    slide_id: str
    filename: str
    extension: str
    path: Path
    batch: str
    cancer_type: str
    file_size_bytes: int
    file_size_gb: float


# =============================================================================
# Inventory
# =============================================================================


def inventory_batch(batch: BatchInfo) -> pd.DataFrame:
    """
    Build a filesystem inventory for a pathology batch.

    Parameters
    ----------
    batch
        Batch information.

    Returns
    -------
    pandas.DataFrame
        One row per slide.
    """

    inventory = []

    for slide in list_slides(batch):

        size_bytes = slide.stat().st_size

        inventory.append(

            SlideInventory(
                slide_id=slide.stem,
                filename=slide.name,
                extension=slide.suffix,
                path=slide,
                batch=batch.name,
                cancer_type=batch.cancer_type,
                file_size_bytes=size_bytes,
                file_size_gb=round(size_bytes / 1024**3, 3),
            )

        )

    return pd.DataFrame(
        asdict(item)
        for item in inventory
    )


# =============================================================================
# Statistics
# =============================================================================


def count_slides(batch: BatchInfo) -> int:
    """
    Return the number of slides in a batch.
    """

    return len(list_slides(batch))


def compute_storage(batch: BatchInfo) -> float:
    """
    Compute total storage occupied by a batch (GB).
    """

    inventory = inventory_batch(batch)

    return inventory["file_size_gb"].sum()


def detect_duplicates(
    inventory: pd.DataFrame,
) -> pd.DataFrame:
    """
    Detect duplicated slide identifiers.

    Parameters
    ----------
    inventory
        Inventory dataframe.

    Returns
    -------
    pandas.DataFrame
        Rows with duplicated slide IDs.
    """

    duplicated = inventory.duplicated(
        subset="slide_id",
        keep=False,
    )

    return inventory.loc[duplicated].sort_values("slide_id")


# =============================================================================
# Export
# =============================================================================


def export_inventory(
    inventory: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Export inventory dataframe.

    Parameters
    ----------
    inventory
        Inventory dataframe.

    output_path
        Destination parquet file.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    inventory.to_parquet(
        output_path,
        index=False,
    )