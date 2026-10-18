"""
General utility functions for the NLST Pathology Exploration project.

Only project-wide helper functions that do not belong to a specific
module should live here.

Avoid placing domain-specific logic in this file.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


# =============================================================================
# Filesystem
# =============================================================================


def ensure_directory(path: Path) -> Path:
    """
    Create a directory if it does not already exist.

    Parameters
    ----------
    path
        Directory path.

    Returns
    -------
    Path
        The same directory path.
    """

    path.mkdir(parents=True, exist_ok=True)
    return path


# =============================================================================
# File Size
# =============================================================================


def bytes_to_kb(size: int) -> float:
    """
    Convert bytes to kilobytes.
    """

    return size / 1024


def bytes_to_mb(size: int) -> float:
    """
    Convert bytes to megabytes.
    """

    return size / 1024**2


def bytes_to_gb(size: int) -> float:
    """
    Convert bytes to gigabytes.
    """

    return size / 1024**3


# =============================================================================
# Time
# =============================================================================


def timestamp() -> str:
    """
    Return the current timestamp.

    Example
    -------
    2026-08-06 18:42:31
    """

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# Logging
# =============================================================================


def print_header(title: str) -> None:
    """
    Print a formatted section header.
    """

    line = "=" * len(title)

    print()
    print(line)
    print(title)
    print(line)


def print_subheader(title: str) -> None:
    """
    Print a formatted subsection header.
    """

    print()
    print(title)
    print("-" * len(title))