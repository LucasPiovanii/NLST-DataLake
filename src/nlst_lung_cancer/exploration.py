"""
Utilities for exploring the NLST Lung Cancer Selection dataset.

This module provides high-level functions to inspect the structure and
metadata of batches, patients, studies, series, and DICOM files.

The functions in this module are intended to support exploratory analysis
in notebooks without coupling the analysis to a specific batch.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

import pandas as pd

from nlst_lung_cancer.io import (
    list_batch_files,
    list_batches,
)
from nlst_lung_cancer.metadata import (
    dicom_dataset_to_dict,
    read_dicom_metadata,
)


# ---------------------------------------------------------------------------
# Batch exploration
# ---------------------------------------------------------------------------


def summarize_batches(
    batches_path: str | Path,
) -> pd.DataFrame:
    """
    Summarize the batches available in a dataset directory.

    Parameters
    ----------
    batches_path:
        Root directory containing the dataset batches.

    Returns
    -------
    pd.DataFrame
        One row per batch with its name and number of DICOM files.
    """
    batches_path = Path(batches_path)

    records = []

    for batch in list_batches(batches_path):
        files = list_batch_files(
            batches_path,
            batch_name=batch.name,
        )

        records.append(
            {
                "batch": batch.name,
                "file_count": len(files),
            }
        )

    return pd.DataFrame(records)


def count_batch_files(
    batches_path: str | Path,
) -> dict[str, int]:
    """
    Count the number of DICOM files in each batch.

    Parameters
    ----------
    batches_path:
        Root directory containing the dataset batches.

    Returns
    -------
    dict[str, int]
        Mapping from batch name to number of files.
    """
    batches_path = Path(batches_path)

    return {
        batch.name: len(
            list_batch_files(
                batches_path,
                batch_name=batch.name,
            )
        )
        for batch in list_batches(batches_path)
    }


# ---------------------------------------------------------------------------
# Directory / hierarchy exploration
# ---------------------------------------------------------------------------


def extract_patient_id_from_path(
    path: str | Path,
) -> str | None:
    """
    Extract the patient identifier from the expected NLST directory structure.

    Expected structure:

        batch/
            sub_batch/
                patient_id/
                    timepoint/
                        series_uid/
                            image.dcm

    Parameters
    ----------
    path:
        Path to a DICOM file.

    Returns
    -------
    str | None
        Patient identifier if the expected structure is present.
    """
    path = Path(path)

    try:
        return path.parents[2].name
    except IndexError:
        return None


def extract_timepoint_from_path(
    path: str | Path,
) -> str | None:
    """
    Extract the timepoint from the expected NLST directory structure.

    Parameters
    ----------
    path:
        Path to a DICOM file.

    Returns
    -------
    str | None
        Timepoint such as T0, T1, etc.
    """
    path = Path(path)

    try:
        return path.parents[1].name
    except IndexError:
        return None


def extract_series_uid_from_path(
    path: str | Path,
) -> str | None:
    """
    Extract the series UID from the expected NLST directory structure.

    Parameters
    ----------
    path:
        Path to a DICOM file.

    Returns
    -------
    str | None
        Series UID from the directory structure.
    """
    path = Path(path)

    try:
        return path.parents[0].name
    except IndexError:
        return None


def build_path_catalog(
    files: Iterable[str | Path],
) -> pd.DataFrame:
    """
    Build a catalog describing the hierarchy of DICOM file paths.

    Parameters
    ----------
    files:
        Iterable of DICOM file paths.

    Returns
    -------
    pd.DataFrame
        Catalog containing batch, sub-batch, patient, timepoint,
        series UID, and file path.
    """
    records = []

    for file_path in files:
        path = Path(file_path)

        records.append(
            {
                "batch": (
                    path.parents[4].name
                    if len(path.parents) > 4
                    else None
                ),
                "sub_batch": (
                    path.parents[3].name
                    if len(path.parents) > 3
                    else None
                ),
                "patient_id": extract_patient_id_from_path(path),
                "timepoint": extract_timepoint_from_path(path),
                "series_uid_from_path": extract_series_uid_from_path(path),
                "filename": path.name,
                "path": str(path),
            }
        )

    return pd.DataFrame(records)


def summarize_path_hierarchy(
    files: Iterable[str | Path],
) -> pd.DataFrame:
    """
    Summarize the hierarchy represented by a collection of DICOM paths.

    The summary includes counts of patients, timepoints, and series.

    Parameters
    ----------
    files:
        Iterable of DICOM file paths.

    Returns
    -------
    pd.DataFrame
        Summary statistics for the provided files.
    """
    catalog = build_path_catalog(files)

    if catalog.empty:
        return pd.DataFrame(
            [
                {
                    "file_count": 0,
                    "patient_count": 0,
                    "timepoint_count": 0,
                    "series_count": 0,
                }
            ]
        )

    return pd.DataFrame(
        [
            {
                "file_count": len(catalog),
                "patient_count": catalog["patient_id"].nunique(),
                "timepoint_count": catalog["timepoint"].nunique(),
                "series_count": catalog["series_uid_from_path"].nunique(),
            }
        ]
    )


# ---------------------------------------------------------------------------
# Patient / timepoint / series exploration
# ---------------------------------------------------------------------------


def count_files_by_patient(
    files: Iterable[str | Path],
) -> pd.DataFrame:
    """
    Count DICOM files associated with each patient.

    Parameters
    ----------
    files:
        Iterable of DICOM file paths.

    Returns
    -------
    pd.DataFrame
        Number of files per patient.
    """
    catalog = build_path_catalog(files)

    return (
        catalog.groupby("patient_id", dropna=False)
        .size()
        .reset_index(name="file_count")
        .sort_values("file_count", ascending=False)
        .reset_index(drop=True)
    )


def count_files_by_timepoint(
    files: Iterable[str | Path],
) -> pd.DataFrame:
    """
    Count DICOM files by timepoint.

    Parameters
    ----------
    files:
        Iterable of DICOM file paths.

    Returns
    -------
    pd.DataFrame
        Number of files per timepoint.
    """
    catalog = build_path_catalog(files)

    return (
        catalog.groupby("timepoint", dropna=False)
        .size()
        .reset_index(name="file_count")
        .sort_values("file_count", ascending=False)
        .reset_index(drop=True)
    )


def count_files_by_series(
    files: Iterable[str | Path],
) -> pd.DataFrame:
    """
    Count DICOM files per series.

    Parameters
    ----------
    files:
        Iterable of DICOM file paths.

    Returns
    -------
    pd.DataFrame
        Number of files per series.
    """
    catalog = build_path_catalog(files)

    return (
        catalog.groupby(
            [
                "patient_id",
                "timepoint",
                "series_uid_from_path",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="file_count")
        .sort_values("file_count", ascending=False)
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# DICOM metadata exploration
# ---------------------------------------------------------------------------


def inspect_dicom_samples(
    files: Iterable[str | Path],
    sample_size: int = 10,
) -> pd.DataFrame:
    """
    Read metadata from a sample of DICOM files.

    Parameters
    ----------
    files:
        Iterable of DICOM file paths.

    sample_size:
        Maximum number of files to inspect.

    Returns
    -------
    pd.DataFrame
        One row per sampled DICOM file containing selected metadata.
    """
    files = list(files)[:sample_size]

    records = []

    for file_path in files:
        dataset = read_dicom_metadata(file_path)

        records.append(
            {
                "path": str(file_path),
                "PatientID": getattr(dataset, "PatientID", None),
                "StudyInstanceUID": getattr(
                    dataset,
                    "StudyInstanceUID",
                    None,
                ),
                "SeriesInstanceUID": getattr(
                    dataset,
                    "SeriesInstanceUID",
                    None,
                ),
                "SOPInstanceUID": getattr(
                    dataset,
                    "SOPInstanceUID",
                    None,
                ),
                "Modality": getattr(dataset, "Modality", None),
                "StudyDate": getattr(dataset, "StudyDate", None),
                "StudyDescription": getattr(
                    dataset,
                    "StudyDescription",
                    None,
                ),
                "SeriesDescription": getattr(
                    dataset,
                    "SeriesDescription",
                    None,
                ),
            }
        )

    return pd.DataFrame(records)


def compare_path_and_dicom_metadata(
    files: Iterable[str | Path],
    sample_size: int = 10,
) -> pd.DataFrame:
    """
    Compare identifiers obtained from the directory hierarchy with
    identifiers stored inside the DICOM metadata.

    Parameters
    ----------
    files:
        Iterable of DICOM file paths.

    sample_size:
        Maximum number of files to inspect.

    Returns
    -------
    pd.DataFrame
        Comparison between path-derived and DICOM-derived identifiers.
    """
    files = list(files)[:sample_size]

    records = []

    for file_path in files:
        path = Path(file_path)
        dataset = read_dicom_metadata(path)

        records.append(
            {
                "path": str(path),
                "path_patient_id": extract_patient_id_from_path(path),
                "dicom_patient_id": getattr(
                    dataset,
                    "PatientID",
                    None,
                ),
                "path_timepoint": extract_timepoint_from_path(path),
                "path_series_uid": extract_series_uid_from_path(path),
                "dicom_series_uid": getattr(
                    dataset,
                    "SeriesInstanceUID",
                    None,
                ),
            }
        )

    return pd.DataFrame(records)


def summarize_dicom_field(
    files: Iterable[str | Path],
    field: str,
    sample_size: int = 100,
) -> pd.DataFrame:
    """
    Summarize the values of a DICOM metadata field over a sample.

    Parameters
    ----------
    files:
        Iterable of DICOM file paths.

    field:
        DICOM keyword to inspect, e.g. ``Modality`` or ``PatientID``.

    sample_size:
        Maximum number of files to inspect.

    Returns
    -------
    pd.DataFrame
        Frequency of each observed value.
    """
    files = list(files)[:sample_size]

    values = []

    for file_path in files:
        dataset = read_dicom_metadata(file_path)
        values.append(getattr(dataset, field, None))

    return (
        pd.Series(values, name=field)
        .value_counts(dropna=False)
        .rename_axis(field)
        .reset_index(name="count")
    )


# ---------------------------------------------------------------------------
# Dataset-level exploration
# ---------------------------------------------------------------------------


def explore_batch(
    batches_path: str | Path,
    batch_name: str,
    sample_size: int = 100,
) -> dict[str, pd.DataFrame]:
    """
    Run a basic exploration of a single batch.

    Parameters
    ----------
    batches_path:
        Root directory containing the batches.

    batch_name:
        Name of the batch to explore.

    sample_size:
        Number of DICOM files to use for metadata inspection.

    Returns
    -------
    dict[str, pd.DataFrame]
        Collection of exploration tables.
    """
    files = list_batch_files(
        batches_path,
        batch_name=batch_name,
    )

    sample_files = files[:sample_size]

    return {
        "hierarchy": summarize_path_hierarchy(files),
        "patients": count_files_by_patient(files),
        "timepoints": count_files_by_timepoint(files),
        "series": count_files_by_series(files),
        "dicom_samples": inspect_dicom_samples(
            sample_files,
            sample_size=sample_size,
        ),
        "path_vs_dicom": compare_path_and_dicom_metadata(
            sample_files,
            sample_size=sample_size,
        ),
    }


def compare_batches(
    batches_path: str | Path,
) -> pd.DataFrame:
    """
    Compare the basic structure of all batches.

    Parameters
    ----------
    batches_path:
        Root directory containing the batches.

    Returns
    -------
    pd.DataFrame
        One row per batch with file, patient, timepoint, and series counts.
    """
    batches_path = Path(batches_path)

    records = []

    for batch in list_batches(batches_path):
        files = list_batch_files(
            batches_path,
            batch_name=batch.name,
        )

        catalog = build_path_catalog(files)

        records.append(
            {
                "batch": batch.name,
                "file_count": len(files),
                "patient_count": catalog["patient_id"].nunique(),
                "timepoint_count": catalog["timepoint"].nunique(),
                "series_count": catalog[
                    "series_uid_from_path"
                ].nunique(),
            }
        )

    return pd.DataFrame(records).sort_values(
        "batch"
    ).reset_index(drop=True)


def build_metadata_catalog(
    files: Iterable[str | Path],
    *,
    include_private: bool = False,
    cancer_category: str | None = None,
) -> pd.DataFrame:
    """
    Build a complete metadata catalog for a collection of DICOM files.

    The catalog contains all DICOM metadata available in each file,
    together with identifiers and information derived from the NLST
    directory structure and the complete path to the DICOM file.

    Parameters
    ----------
    files
        Iterable of DICOM file paths.
    include_private
        Whether private DICOM tags should be included.
    cancer_category
        Category label to add to every row (e.g. "screen_detected", "other").

    Returns
    -------
    pd.DataFrame
        One row per DICOM file.
    """
    records = []

    for file_path in files:
        path = Path(file_path)

        dataset = read_dicom_metadata(path)

        metadata = dicom_dataset_to_dict(
            dataset,
            include_private=include_private,
        )

        metadata.update(
            {
                "cancer_category": cancer_category,
                "patient_id": extract_patient_id_from_path(path),
                "batch": (
                    path.parents[4].name
                    if len(path.parents) > 4
                    else None
                ),
                "sub_batch": (
                    path.parents[3].name
                    if len(path.parents) > 3
                    else None
                ),
                "timepoint": extract_timepoint_from_path(path),
                "series_uid_from_path": extract_series_uid_from_path(path),
                "filename": path.name,
                "path": str(path),
            }
        )

        records.append(metadata)

    return pd.DataFrame(records)