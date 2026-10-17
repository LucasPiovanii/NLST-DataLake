"""
Visualization utilities for NLST pathology slides.

This module contains helper functions for generating visual
representations of Whole Slide Images (WSIs). These functions
are intended for exploratory analysis and quality control.

No metadata extraction or catalog manipulation is performed here.
"""

from __future__ import annotations

from math import ceil
from pathlib import Path
import pandas as pd

import matplotlib.pyplot as plt
from PIL import Image

import openslide

from .config import THUMBNAIL_SIZE

from .slide import open_slide
from .slide import close_slide


# =============================================================================
# Thumbnail Generation
# =============================================================================


def generate_thumbnail(
    slide: openslide.OpenSlide,
    size: tuple[int, int] = THUMBNAIL_SIZE,
) -> Image.Image:
    """
    Generate a thumbnail from a Whole Slide Image.

    Parameters
    ----------
    slide
        OpenSlide object.

    size
        Thumbnail size in pixels.

    Returns
    -------
    PIL.Image.Image
    """

    return slide.get_thumbnail(size)


# =============================================================================
# Saving
# =============================================================================


def save_thumbnail(
    thumbnail: Image.Image,
    output_path: Path,
) -> None:
    """
    Save a thumbnail to disk.

    Parameters
    ----------
    thumbnail
        PIL Image.

    output_path
        Destination image.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    thumbnail.save(output_path)


# =============================================================================
# Display
# =============================================================================


def show_thumbnail(
    thumbnail: Image.Image,
    title: str | None = None,
    figsize: tuple[int, int] = (6, 6),
) -> None:
    """
    Display a thumbnail.
    """

    plt.figure(figsize=figsize)

    plt.imshow(thumbnail)

    if title is not None:
        plt.title(title)

    plt.axis("off")

    plt.tight_layout()

    plt.show()


# =============================================================================
# Contact Sheet
# =============================================================================


def make_contact_sheet(
    thumbnails: list[Image.Image],
    columns: int = 5,
) -> Image.Image:
    """
    Create a contact sheet from multiple thumbnails.

    Parameters
    ----------
    thumbnails
        List of PIL Images.

    columns
        Number of columns.

    Returns
    -------
    PIL.Image.Image
    """

    if len(thumbnails) == 0:
        raise ValueError("Thumbnail list is empty.")

    thumb_width, thumb_height = thumbnails[0].size

    rows = ceil(len(thumbnails) / columns)

    canvas = Image.new(
        "RGB",
        (
            columns * thumb_width,
            rows * thumb_height,
        ),
        color="white",
    )

    for index, thumbnail in enumerate(thumbnails):

        row = index // columns
        column = index % columns

        canvas.paste(
            thumbnail,
            (
                column * thumb_width,
                row * thumb_height,
            ),
        )

    return canvas


# =============================================================================
# Convenience
# =============================================================================


def save_contact_sheet(
    contact_sheet: Image.Image,
    output_path: Path,
) -> None:
    """
    Save a contact sheet.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    contact_sheet.save(output_path)


# =============================================================================
# Slide Grid
# =============================================================================


def show_largest_slides(
    catalog: pd.DataFrame,
    n: int = 25,
    columns: int = 5,
    thumbnail_size: tuple[int, int] = (256, 256),
    figsize: tuple[int, int] | None = None,
) -> None:
    """
    Display the largest slides (by file size) as a thumbnail grid.

    Parameters
    ----------
    catalog
        Metadata catalog generated from the pathology batches.

    n
        Number of slides to display.

    columns
        Number of columns in the grid.

    thumbnail_size
        Size of each generated thumbnail.

    figsize
        Optional matplotlib figure size.
    """

    if "file_size_mb" not in catalog.columns:
        raise ValueError(
            "Catalog must contain a 'file_size_mb' column."
        )

    slides = (
        catalog
        .sort_values("file_size_mb", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )

    rows = ceil(len(slides) / columns)

    if figsize is None:
        figsize = (
            columns * 3.5,
            rows * 3.5,
        )

    fig, axes = plt.subplots(
        rows,
        columns,
        figsize=figsize,
    )

    axes = axes.flatten()

    for ax in axes:
        ax.axis("off")

    for ax, (_, row) in zip(axes, slides.iterrows()):

        slide = open_slide(Path(row["path"]))

        thumbnail = generate_thumbnail(
            slide,
            size=thumbnail_size,
        )

        ax.imshow(thumbnail)

        ax.set_title(
            (
                f"{row['slide_id']}\n"
                f"{row['file_size_mb']:.1f} MB"
            ),
            fontsize=8,
        )

        ax.axis("off")

        close_slide(slide)

    plt.tight_layout()
    plt.show()