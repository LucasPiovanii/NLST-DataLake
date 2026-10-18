"""
I/O utilities for the NLST Lung Cancer dataset.

This module provides functions for discovering, loading, and inspecting
DICOM files organized in batches.
"""

from pathlib import Path
from typing import Iterable

import pydicom


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def list_batches(dataset_path: str | Path) -> list[Path]:
    """
    List all batch directories in a lung cancer dataset.

    Parameters
    ----------
    dataset_path
        Root directory containing the dataset batches.

    Returns
    -------
    list[pathlib.Path]
        Sorted list of batch directories.
    """
    dataset_path = Path(dataset_path)

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset path does not exist: {dataset_path}"
        )

    if not dataset_path.is_dir():
        raise NotADirectoryError(
            f"Dataset path is not a directory: {dataset_path}"
        )

    return sorted(
        path
        for path in dataset_path.iterdir()
        if path.is_dir()
    )


def list_files(
    path: str | Path,
    pattern: str = "*",
    recursive: bool = False,
) -> list[Path]:
    """
    List files matching a pattern.

    Parameters
    ----------
    path
        Directory to search.
    pattern
        Glob pattern used to filter files.
    recursive
        Whether to search recursively.

    Returns
    -------
    list[pathlib.Path]
        Sorted list of matching files.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Path does not exist: {path}"
        )

    if not path.is_dir():
        raise NotADirectoryError(
            f"Path is not a directory: {path}"
        )

    if recursive:
        files = path.rglob(pattern)
    else:
        files = path.glob(pattern)

    return sorted(
        file
        for file in files
        if file.is_file()
    )


def list_dicom_files(
    path: str | Path,
    recursive: bool = True,
) -> list[Path]:
    """
    List DICOM files in a dataset directory.

    The function currently relies on common DICOM file extensions and
    does not attempt to parse every file to determine whether it is
    a valid DICOM object.

    Parameters
    ----------
    path
        Directory containing DICOM files.
    recursive
        Whether to search recursively.

    Returns
    -------
    list[pathlib.Path]
        Sorted list of DICOM file paths.
    """
    path = Path(path)

    extensions = {
        ".dcm",
        ".dicom",
    }

    if recursive:
        candidates = path.rglob("*")
    else:
        candidates = path.glob("*")

    return sorted(
        file
        for file in candidates
        if file.is_file()
        and file.suffix.lower() in extensions
    )


# ---------------------------------------------------------------------------
# Batch loading
# ---------------------------------------------------------------------------


def get_batch(
    dataset_path: str | Path,
    batch_name: str,
) -> Path:
    """
    Return the path of a specific batch.

    Parameters
    ----------
    dataset_path
        Root directory containing the dataset batches.
    batch_name
        Name of the batch.

    Returns
    -------
    pathlib.Path
        Path to the requested batch.
    """
    dataset_path = Path(dataset_path)
    batch_path = dataset_path / batch_name

    if not batch_path.exists():
        raise FileNotFoundError(
            f"Batch '{batch_name}' does not exist under {dataset_path}"
        )

    if not batch_path.is_dir():
        raise NotADirectoryError(
            f"Batch path is not a directory: {batch_path}"
        )

    return batch_path


def list_batch_files(
    dataset_path: str | Path,
    batch_name: str,
    pattern: str = "*",
    recursive: bool = True,
) -> list[Path]:
    """
    List files belonging to a specific batch.

    Parameters
    ----------
    dataset_path
        Root directory containing the dataset batches.
    batch_name
        Name of the batch.
    pattern
        Glob pattern used to filter files.
    recursive
        Whether to search recursively.

    Returns
    -------
    list[pathlib.Path]
        Sorted list of files.
    """
    batch_path = get_batch(
        dataset_path,
        batch_name,
    )

    return list_files(
        batch_path,
        pattern=pattern,
        recursive=recursive,
    )


# ---------------------------------------------------------------------------
# Dataset utilities
# ---------------------------------------------------------------------------


def count_files(
    path: str | Path,
    pattern: str = "*",
    recursive: bool = True,
) -> int:
    """
    Count files matching a pattern.

    Parameters
    ----------
    path
        Directory to search.
    pattern
        Glob pattern used to filter files.
    recursive
        Whether to search recursively.

    Returns
    -------
    int
        Number of matching files.
    """
    return len(
        list_files(
            path,
            pattern=pattern,
            recursive=recursive,
        )
    )


def get_file_sizes(
    files: Iterable[str | Path],
) -> dict[str, int]:
    """
    Return file sizes in bytes.

    Parameters
    ----------
    files
        Iterable of file paths.

    Returns
    -------
    dict[str, int]
        Mapping from file path to size in bytes.
    """
    return {
        str(Path(file)): Path(file).stat().st_size
        for file in files
    }