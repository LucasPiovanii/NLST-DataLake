"""
Utilities for discovering NLST pathology datasets.

This module is responsible only for navigating the directory
structure of the NLST pathology collection.

It does NOT inspect slide contents or metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from statistics import mean
from statistics import median
from statistics import stdev

from .config import PATHOLOGY_ROOT


@dataclass(frozen=True)
class BatchInfo:
    """
    Information describing a pathology batch.
    """

    name: str
    cancer_type: str
    path: Path


def list_cancer_types(root: Path = PATHOLOGY_ROOT) -> list[str]:
    """
    List all available cancer type folders.

    Returns
    -------
    list[str]
        Example:
        [
            "2-1-Adenocarcinoma",
            "2-2-Squamous-Cell-Carcinoma",
            ...
        ]
    """

    return sorted(
        directory.name
        for directory in root.iterdir()
        if directory.is_dir()
    )


def list_batches(root: Path = PATHOLOGY_ROOT) -> list[str]:
    """
    List all pathology batches.

    Returns
    -------
    list[str]
        Example:
        [
            "batch1",
            "batch2",
            ...
            "batch9",
        ]
    """

    batches = []

    for cancer_type in root.iterdir():

        if not cancer_type.is_dir():
            continue

        for batch in cancer_type.iterdir():

            if batch.is_dir():
                batches.append(batch.name)

    return sorted(batches)


def batch_exists(
    batch_name: str,
    root: Path = PATHOLOGY_ROOT,
) -> bool:
    """
    Check whether a pathology batch exists.
    """

    try:
        get_batch(batch_name, root)
        return True

    except FileNotFoundError:
        return False


def get_batch(
    batch_name: str,
    root: Path = PATHOLOGY_ROOT,
) -> BatchInfo:
    """
    Retrieve information about a pathology batch.

    Parameters
    ----------
    batch_name
        Batch name (e.g. batch1).

    Returns
    -------
    BatchInfo
    """

    for cancer_type in root.iterdir():

        if not cancer_type.is_dir():
            continue

        candidate = cancer_type / batch_name

        if candidate.exists():

            return BatchInfo(
                name=batch_name,
                cancer_type=cancer_type.name,
                path=candidate,
            )

    raise FileNotFoundError(
        f"Batch '{batch_name}' was not found inside {root}"
    )


def list_slides(batch: BatchInfo) -> list[Path]:
    """
    List all SVS slides contained in a batch.

    Parameters
    ----------
    batch
        Batch information.

    Returns
    -------
    list[Path]
    """

    return sorted(batch.path.glob("*.svs"))


def dataset_summary(batch: BatchInfo) -> dict:
    """
    Generate a summary describing a pathology batch.

    Parameters
    ----------
    batch
        Batch information.

    Returns
    -------
    dict
        Summary statistics for the batch.
    """

    slides = list_slides(batch)

    file_sizes = [
        slide.stat().st_size
        for slide in slides
    ]

    total_size = sum(file_sizes)

    file_sizes_mb = [
        size / 1024**2
        for size in file_sizes
    ]

    return {
        "batch": batch.name,
        "cancer_type": batch.cancer_type,
        "path": batch.path,

        "n_slides": len(slides),

        "total_size_bytes": total_size,
        "total_size_gb": round(total_size / 1024**3, 2),

        "mean_slide_size_mb": round(mean(file_sizes_mb), 2),
        "median_slide_size_mb": round(median(file_sizes_mb), 2),
        "min_slide_size_mb": round(min(file_sizes_mb), 2),
        "max_slide_size_mb": round(max(file_sizes_mb), 2),
        "std_slide_size_mb": (
            round(stdev(file_sizes_mb), 2)
            if len(file_sizes_mb) > 1
            else 0.0
        ),
    }