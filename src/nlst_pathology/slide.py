"""
Utilities for interacting with Whole Slide Images (SVS).

This module wraps OpenSlide and exposes convenience functions
for reading metadata and image properties from a single slide.

It intentionally does not perform any batch-level operations.
"""

from __future__ import annotations

from pathlib import Path

import openslide

from .config import OPENSLIDE_KEYS
from .config import APERIO_KEYS


# =============================================================================
# Opening / Closing
# =============================================================================


def open_slide(path: Path) -> openslide.OpenSlide:
    """
    Open a Whole Slide Image.

    Parameters
    ----------
    path
        Path to a .svs file.

    Returns
    -------
    openslide.OpenSlide
    """

    return openslide.OpenSlide(str(path))


# =============================================================================
# Basic Information
# =============================================================================


def get_dimensions(
    slide: openslide.OpenSlide,
) -> tuple[int, int]:
    """
    Return the full-resolution dimensions.
    """

    return slide.dimensions


def get_level_count(
    slide: openslide.OpenSlide,
) -> int:
    """
    Return the number of pyramid levels.
    """

    return slide.level_count


def get_level_dimensions(
    slide: openslide.OpenSlide,
) -> list[tuple[int, int]]:
    """
    Return dimensions of every pyramid level.
    """

    return list(slide.level_dimensions)


def get_level_downsamples(
    slide: openslide.OpenSlide,
) -> list[float]:
    """
    Return downsample factor of every pyramid level.
    """

    return list(slide.level_downsamples)


# =============================================================================
# Metadata
# =============================================================================


def get_properties(
    slide: openslide.OpenSlide,
) -> dict[str, str]:
    """
    Return all OpenSlide properties.
    """

    return dict(slide.properties)


def extract_openslide_metadata(
    slide: openslide.OpenSlide,
) -> dict:
    """
    Extract standard OpenSlide metadata.
    """

    props = slide.properties

    return {
        key: props.get(key)
        for key in OPENSLIDE_KEYS
    }


def extract_aperio_metadata(
    slide: openslide.OpenSlide,
) -> dict:
    """
    Extract Aperio-specific metadata.
    """

    props = slide.properties

    return {
        key: props.get(key)
        for key in APERIO_KEYS
    }


# =============================================================================
# Convenience
# =============================================================================


def summarize_slide(
    slide: openslide.OpenSlide,
) -> dict:
    """
    Return a lightweight summary of a slide.
    """

    width, height = slide.dimensions

    return {
        "vendor": slide.properties.get("openslide.vendor"),
        "width": width,
        "height": height,
        "levels": slide.level_count,
    }


# =============================================================================
# Cleanup
# =============================================================================


def close_slide(
    slide: openslide.OpenSlide,
) -> None:
    """
    Close an OpenSlide object.
    """

    slide.close()