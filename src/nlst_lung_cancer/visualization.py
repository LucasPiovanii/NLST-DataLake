"""
Visualization utilities for the NLST Lung Cancer Selection dataset.

This module provides functions to visualize DICOM images and samples
of the dataset during exploratory analysis.

The functions in this module are intended to be used primarily from
Jupyter notebooks.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pydicom


# ---------------------------------------------------------------------------
# DICOM loading
# ---------------------------------------------------------------------------


def load_dicom_image(
    path: str | Path,
) -> tuple[pydicom.Dataset, np.ndarray]:
    """
    Load a DICOM file and return its dataset and pixel array.

    Parameters
    ----------
    path:
        Path to the DICOM file.

    Returns
    -------
    tuple[pydicom.Dataset, np.ndarray]
        DICOM dataset and image pixel array.
    """
    path = Path(path)

    dataset = pydicom.dcmread(path)
    image = dataset.pixel_array

    return dataset, image


# ---------------------------------------------------------------------------
# Image size utilities
# ---------------------------------------------------------------------------


def get_image_size(
    path: str | Path,
) -> int:
    """
    Return the number of pixels in a DICOM image.

    Parameters
    ----------
    path:
        Path to the DICOM file.

    Returns
    -------
    int
        Number of pixels (Rows × Columns).
    """
    dataset = pydicom.dcmread(
        path,
        stop_before_pixels=True,
    )

    rows = int(getattr(dataset, "Rows", 0))
    columns = int(getattr(dataset, "Columns", 0))

    return rows * columns


def get_file_size(
    path: str | Path,
) -> int:
    """
    Return the DICOM file size in bytes.

    Parameters
    ----------
    path:
        Path to the DICOM file.

    Returns
    -------
    int
        File size in bytes.
    """
    return Path(path).stat().st_size


def rank_images_by_size(
    files: Iterable[str | Path],
    by: str = "file_size",
    descending: bool = True,
) -> list[Path]:
    """
    Rank DICOM images by file size or image dimensions.

    Parameters
    ----------
    files:
        Iterable of DICOM file paths.

    by:
        Ranking criterion:

        - ``"file_size"``: size of the DICOM file in bytes.
        - ``"pixel_count"``: Rows × Columns.

    descending:
        Whether to sort from largest to smallest.

    Returns
    -------
    list[Path]
        Sorted list of DICOM paths.
    """
    files = [Path(path) for path in files]

    if by == "file_size":
        key_function = get_file_size

    elif by == "pixel_count":
        key_function = get_image_size

    else:
        raise ValueError(
            "Invalid 'by'. Use 'file_size' or 'pixel_count'."
        )

    return sorted(
        files,
        key=key_function,
        reverse=descending,
    )


# ---------------------------------------------------------------------------
# Individual image visualization
# ---------------------------------------------------------------------------


def show_dicom(
    path: str | Path,
    figsize: tuple[float, float] = (8, 8),
    cmap: str = "gray",
    title: str | None = None,
    show_axes: bool = False,
) -> None:
    """
    Display a single DICOM image.

    Parameters
    ----------
    path:
        Path to the DICOM file.

    figsize:
        Matplotlib figure size.

    cmap:
        Matplotlib colormap.

    title:
        Optional custom title. If omitted, the filename is used.

    show_axes:
        Whether to display image axes.
    """
    dataset, image = load_dicom_image(path)

    plt.figure(figsize=figsize)

    plt.imshow(
        image,
        cmap=cmap,
    )

    if title is None:
        title = Path(path).name

    plt.title(title)

    if not show_axes:
        plt.axis("off")

    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# DICOM metadata helpers
# ---------------------------------------------------------------------------


def _format_metadata_value(
    value: object,
    max_length: int = 40,
) -> str:
    """
    Convert a metadata value into a compact display string.
    """
    value = str(value)

    if len(value) > max_length:
        return value[: max_length - 3] + "..."

    return value


def _build_image_title(
    path: str | Path,
    dataset: pydicom.Dataset,
    show_patient: bool = True,
    show_series: bool = False,
    show_instance: bool = False,
) -> str:
    """
    Build a compact title for a DICOM image.
    """
    parts = [Path(path).name]

    if show_patient:
        patient_id = getattr(dataset, "PatientID", None)

        if patient_id is not None:
            parts.append(
                f"Patient: {_format_metadata_value(patient_id)}"
            )

    if show_series:
        series_description = getattr(
            dataset,
            "SeriesDescription",
            None,
        )

        if series_description is not None:
            parts.append(
                f"Series: {_format_metadata_value(series_description)}"
            )

    if show_instance:
        instance_number = getattr(
            dataset,
            "InstanceNumber",
            None,
        )

        if instance_number is not None:
            parts.append(
                f"Instance: {instance_number}"
            )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Grid visualization
# ---------------------------------------------------------------------------


def show_image_grid(
    files: Iterable[str | Path],
    n: int = 9,
    columns: int = 3,
    figsize_per_image: tuple[float, float] = (5, 5),
    cmap: str = "gray",
    sort_by: str | None = None,
    descending: bool = True,
    show_titles: bool = True,
    show_axes: bool = False,
    show_patient: bool = True,
    show_series: bool = False,
    show_instance: bool = False,
) -> None:
    """
    Display a selection of DICOM images in a grid.

    Parameters
    ----------
    files:
        Iterable of DICOM file paths.

    n:
        Maximum number of images to display.

    columns:
        Number of columns in the grid.

    figsize_per_image:
        Figure size allocated to each image.

    cmap:
        Matplotlib colormap.

    sort_by:
        Optional ranking criterion:

        - ``"file_size"``: rank by DICOM file size.
        - ``"pixel_count"``: rank by Rows × Columns.

        If ``None``, the original order is preserved.

    descending:
        Whether ranking should be descending.

    show_titles:
        Whether to display image titles.

    show_axes:
        Whether to display image axes.

    show_patient:
        Whether to include PatientID in titles.

    show_series:
        Whether to include SeriesDescription in titles.

    show_instance:
        Whether to include InstanceNumber in titles.
    """
    files = [Path(path) for path in files]

    if not files:
        raise ValueError("No DICOM files were provided.")

    if n <= 0:
        raise ValueError("'n' must be greater than zero.")

    if columns <= 0:
        raise ValueError("'columns' must be greater than zero.")

    if sort_by is not None:
        files = rank_images_by_size(
            files,
            by=sort_by,
            descending=descending,
        )

    files = files[:n]

    rows = math.ceil(len(files) / columns)

    figsize = (
        columns * figsize_per_image[0],
        rows * figsize_per_image[1],
    )

    fig, axes = plt.subplots(
        rows,
        columns,
        figsize=figsize,
        squeeze=False,
    )

    axes = axes.flatten()

    for index, path in enumerate(files):
        ax = axes[index]

        try:
            dataset, image = load_dicom_image(path)

            ax.imshow(
                image,
                cmap=cmap,
            )

            if show_titles:
                title = _build_image_title(
                    path,
                    dataset,
                    show_patient=show_patient,
                    show_series=show_series,
                    show_instance=show_instance,
                )

                ax.set_title(title)

        except Exception as exc:
            ax.text(
                0.5,
                0.5,
                f"Could not load image\n{exc}",
                ha="center",
                va="center",
            )

        if not show_axes:
            ax.axis("off")

    # Hide unused axes.
    for ax in axes[len(files):]:
        ax.axis("off")

    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# Top-N visualization
# ---------------------------------------------------------------------------


def show_largest_images(
    files: Iterable[str | Path],
    n: int = 9,
    columns: int = 3,
    by: str = "file_size",
    figsize_per_image: tuple[float, float] = (5, 5),
    cmap: str = "gray",
    show_patient: bool = True,
    show_series: bool = False,
    show_instance: bool = False,
) -> None:
    """
    Display the N largest DICOM images in a grid.

    Parameters
    ----------
    files:
        Iterable of DICOM file paths.

    n:
        Number of largest images to display.

    columns:
        Number of columns in the grid.

    by:
        Criterion used to define "largest":

        - ``"file_size"``: largest DICOM files.
        - ``"pixel_count"``: largest image dimensions.

    figsize_per_image:
        Figure size allocated to each image.

    cmap:
        Matplotlib colormap.

    show_patient:
        Whether to include PatientID in titles.

    show_series:
        Whether to include SeriesDescription in titles.

    show_instance:
        Whether to include InstanceNumber in titles.
    """
    show_image_grid(
        files=files,
        n=n,
        columns=columns,
        figsize_per_image=figsize_per_image,
        cmap=cmap,
        sort_by=by,
        descending=True,
        show_titles=True,
        show_axes=False,
        show_patient=show_patient,
        show_series=show_series,
        show_instance=show_instance,
    )


# ---------------------------------------------------------------------------
# Random sample visualization
# ---------------------------------------------------------------------------


def show_random_sample(
    files: Iterable[str | Path],
    n: int = 9,
    columns: int = 3,
    random_state: int | None = None,
    figsize_per_image: tuple[float, float] = (5, 5),
    cmap: str = "gray",
    show_patient: bool = True,
    show_series: bool = False,
    show_instance: bool = False,
) -> None:
    """
    Display a random sample of DICOM images in a grid.

    Parameters
    ----------
    files:
        Iterable of DICOM file paths.

    n:
        Number of images to display.

    columns:
        Number of columns in the grid.

    random_state:
        Optional random seed for reproducibility.

    figsize_per_image:
        Figure size allocated to each image.

    cmap:
        Matplotlib colormap.

    show_patient:
        Whether to include PatientID in titles.

    show_series:
        Whether to include SeriesDescription in titles.

    show_instance:
        Whether to include InstanceNumber in titles.
    """
    files = [Path(path) for path in files]

    if not files:
        raise ValueError("No DICOM files were provided.")

    if n <= 0:
        raise ValueError("'n' must be greater than zero.")

    rng = np.random.default_rng(random_state)

    sample_size = min(n, len(files))

    indices = rng.choice(
        len(files),
        size=sample_size,
        replace=False,
    )

    sample_files = [
        files[index]
        for index in indices
    ]

    show_image_grid(
        files=sample_files,
        n=sample_size,
        columns=columns,
        figsize_per_image=figsize_per_image,
        cmap=cmap,
        show_titles=True,
        show_axes=False,
        show_patient=show_patient,
        show_series=show_series,
        show_instance=show_instance,
    )


# ---------------------------------------------------------------------------
# Series visualization
# ---------------------------------------------------------------------------


def show_series_sample(
    files: Iterable[str | Path],
    n: int = 9,
    columns: int = 3,
    figsize_per_image: tuple[float, float] = (5, 5),
    cmap: str = "gray",
    sort_by_instance: bool = True,
) -> None:
    """
    Display a sample of images from a single DICOM series.

    Parameters
    ----------
    files:
        Iterable of DICOM files belonging to the same series.

    n:
        Number of images to display.

    columns:
        Number of columns in the grid.

    figsize_per_image:
        Figure size allocated to each image.

    cmap:
        Matplotlib colormap.

    sort_by_instance:
        Whether to sort images by DICOM InstanceNumber.
    """
    files = [Path(path) for path in files]

    if not files:
        raise ValueError("No DICOM files were provided.")

    if sort_by_instance:
        records = []

        for path in files:
            dataset = pydicom.dcmread(
                path,
                stop_before_pixels=True,
            )

            instance_number = getattr(
                dataset,
                "InstanceNumber",
                0,
            )

            records.append(
                (
                    path,
                    instance_number,
                )
            )

        records.sort(
            key=lambda item: item[1]
        )

        files = [
            path
            for path, _ in records
        ]

    # Select approximately evenly distributed slices instead of only
    # taking the first N files.
    if len(files) > n:
        indices = np.linspace(
            0,
            len(files) - 1,
            n,
            dtype=int,
        )

        files = [
            files[index]
            for index in indices
        ]

    show_image_grid(
        files=files,
        n=len(files),
        columns=columns,
        figsize_per_image=figsize_per_image,
        cmap=cmap,
        show_titles=True,
        show_axes=False,
        show_patient=True,
        show_series=True,
        show_instance=True,
    )