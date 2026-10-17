from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import json

import pydicom
from pydicom.dataset import FileDataset
from pydicom.multival import MultiValue
from pydicom.sequence import Sequence
from pydicom.valuerep import PersonName


# =============================================================================
# DICOM READING
# =============================================================================


def read_dicom_metadata(
    dicom_path: str | Path,
    *,
    stop_before_pixels: bool = True,
) -> pydicom.Dataset:
    """
    Read a DICOM file and return its metadata.

    Parameters
    ----------
    dicom_path
        Path to the DICOM file.
    stop_before_pixels
        If True, pixel data is not loaded. This is recommended when
        the objective is only to inspect metadata.

    Returns
    -------
    pydicom.Dataset
        DICOM dataset containing the metadata.
    """
    dicom_path = Path(dicom_path)

    if not dicom_path.exists():
        raise FileNotFoundError(f"DICOM file not found: {dicom_path}")

    if not dicom_path.is_file():
        raise ValueError(f"Path is not a file: {dicom_path}")

    return pydicom.dcmread(
        dicom_path,
        stop_before_pixels=stop_before_pixels,
    )


def read_dicom(
    path: str | Path,
    *,
    stop_before_pixels: bool = False,
) -> FileDataset:
    """
    Read a DICOM file.

    Parameters
    ----------
    path
        Path to the DICOM file.
    stop_before_pixels
        If True, do not load pixel data. This is useful when exploring
        metadata and avoids loading potentially large image arrays.

    Returns
    -------
    pydicom.dataset.FileDataset
        Loaded DICOM dataset.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"DICOM file does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"DICOM path is not a file: {path}"
        )

    return pydicom.dcmread(
        path,
        stop_before_pixels=stop_before_pixels,
    )


# =============================================================================
# TAG UTILITIES
# =============================================================================


def _dicom_value_to_python(value):
    """
    Convert a pydicom value into a Parquet-compatible Python value.

    Scalar values are preserved as scalars. Multi-valued and sequence
    values are serialized as JSON strings to guarantee a consistent
    column type across DICOM files.
    """
    if value is None:
        return None

    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.decode("latin-1", errors="replace")

    if isinstance(value, PersonName):
        return str(value)

    if isinstance(value, (MultiValue, list, tuple)):
        return json.dumps(
            [
                _dicom_value_to_python(item)
                for item in value
            ],
            ensure_ascii=False,
        )

    if isinstance(value, Sequence):
        return json.dumps(
            [
                {
                    element.keyword or str(element.tag):
                    _dicom_value_to_python(element.value)
                    for element in item
                }
                for item in value
            ],
            ensure_ascii=False,
        )

    if isinstance(value, pydicom.dataset.Dataset):
        return json.dumps(
            {
                element.keyword or str(element.tag):
                _dicom_value_to_python(element.value)
                for element in value
            },
            ensure_ascii=False,
        )

    return value


def normalize_catalog_for_parquet(
    catalog: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize metadata columns with heterogeneous Python types.
    """
    catalog = catalog.copy()

    for column in catalog.columns:
        non_null = catalog[column].dropna()

        if non_null.empty:
            continue

        if non_null.map(type).nunique() > 1:
            catalog[column] = catalog[column].astype("string")

    return catalog


def dicom_dataset_to_dict(
    dataset: pydicom.Dataset,
    *,
    include_private: bool = False,
) -> dict:
    """
    Convert a DICOM Dataset into a dictionary.

    Parameters
    ----------
    dataset
        DICOM dataset.
    include_private
        Whether private DICOM tags should be included.

    Returns
    -------
    dict
        Dictionary containing DICOM metadata.
    """
    metadata = {}

    for element in dataset:
        if element.tag.is_private and not include_private:
            continue

        keyword = element.keyword

        if keyword:
            key = keyword
        else:
            key = str(element.tag)

        metadata[key] = _dicom_value_to_python(element.value)

    return metadata


def get_dicom_tags(
    dicom_path: str | Path,
    *,
    include_private: bool = False,
) -> dict:
    """
    Read a DICOM file and return its metadata as a dictionary.

    Parameters
    ----------
    dicom_path
        Path to the DICOM file.
    include_private
        Whether private DICOM tags should be included.

    Returns
    -------
    dict
        DICOM metadata.
    """
    dataset = read_dicom_metadata(dicom_path)

    return dicom_dataset_to_dict(
        dataset,
        include_private=include_private,
    )


# =============================================================================
# SELECTED / COMMON METADATA
# =============================================================================


DEFAULT_METADATA_FIELDS = [
    "PatientID",
    "PatientName",
    "PatientSex",
    "PatientBirthDate",
    "StudyInstanceUID",
    "SeriesInstanceUID",
    "SOPInstanceUID",
    "StudyDate",
    "StudyTime",
    "Modality",
    "Manufacturer",
    "ManufacturerModelName",
    "InstitutionName",
    "StudyDescription",
    "SeriesDescription",
    "BodyPartExamined",
    "SliceThickness",
    "SpacingBetweenSlices",
    "PixelSpacing",
    "Rows",
    "Columns",
    "BitsAllocated",
    "BitsStored",
    "HighBit",
    "PixelRepresentation",
    "RescaleIntercept",
    "RescaleSlope",
    "KVP",
    "Exposure",
]


def extract_selected_metadata(
    dicom_path: str | Path,
    fields: Iterable[str] | None = None,
) -> dict:
    """
    Extract selected metadata fields from a DICOM file.

    Parameters
    ----------
    dicom_path
        Path to the DICOM file.
    fields
        Metadata fields to extract. If None, DEFAULT_METADATA_FIELDS
        is used.

    Returns
    -------
    dict
        Dictionary containing the requested fields.
    """
    dataset = read_dicom_metadata(dicom_path)

    if fields is None:
        fields = DEFAULT_METADATA_FIELDS

    metadata = {}

    for field in fields:
        value = getattr(dataset, field, None)
        metadata[field] = _dicom_value_to_python(value)

    return metadata


# =============================================================================
# DIRECTORY EXPLORATION
# =============================================================================


def inspect_dicom_file(
    dicom_path: str | Path,
    *,
    include_private: bool = False,
) -> pd.DataFrame:
    """
    Return all metadata from a DICOM file as a tabular representation.

    Parameters
    ----------
    dicom_path
        Path to the DICOM file.
    include_private
        Whether private DICOM tags should be included.

    Returns
    -------
    pandas.DataFrame
        One row per DICOM metadata element.
    """
    dataset = read_dicom_metadata(dicom_path)

    records = []

    for element in dataset:
        if element.tag.is_private and not include_private:
            continue

        records.append(
            {
                "tag": str(element.tag),
                "keyword": element.keyword,
                "name": element.name,
                "vr": element.VR,
                "value": _dicom_value_to_python(element.value),
                "is_private": element.tag.is_private,
            }
        )

    return pd.DataFrame(records)


def build_metadata_catalog(
    dicom_paths: Iterable[str | Path],
    *,
    include_private: bool = False,
) -> pd.DataFrame:
    """
    Build a metadata catalog from multiple DICOM files.

    Each row corresponds to one DICOM file.

    Parameters
    ----------
    dicom_paths
        Iterable containing paths to DICOM files.
    include_private
        Whether private DICOM tags should be included.

    Returns
    -------
    pandas.DataFrame
        One row per DICOM file.
    """
    records = []

    for dicom_path in dicom_paths:
        dicom_path = Path(dicom_path)

        try:
            metadata = get_dicom_tags(
                dicom_path,
                include_private=include_private,
            )

            metadata = {
                "filename": dicom_path.name,
                "path": str(dicom_path),
                **metadata,
            }

            records.append(metadata)

        except Exception as exc:
            records.append(
                {
                    "filename": dicom_path.name,
                    "path": str(dicom_path),
                    "metadata_error": str(exc),
                }
            )

    return pd.DataFrame(records)


# =============================================================================
# SUMMARY / EXPLORATION
# =============================================================================


def summarize_metadata_catalog(
    catalog: pd.DataFrame,
) -> pd.DataFrame:
    """
    Summarize the completeness of metadata fields.

    Parameters
    ----------
    catalog
        Metadata catalog generated by build_metadata_catalog.

    Returns
    -------
    pandas.DataFrame
        Summary containing non-null counts and percentages.
    """
    total_rows = len(catalog)

    if total_rows == 0:
        return pd.DataFrame(
            columns=[
                "field",
                "non_null",
                "null",
                "non_null_pct",
                "unique_values",
            ]
        )

    summary = []

    for column in catalog.columns:
        non_null = catalog[column].notna().sum()
        null = catalog[column].isna().sum()
        unique_values = catalog[column].nunique(dropna=True)

        summary.append(
            {
                "field": column,
                "non_null": non_null,
                "null": null,
                "non_null_pct": 100 * non_null / total_rows,
                "unique_values": unique_values,
            }
        )

    return (
        pd.DataFrame(summary)
        .sort_values(
            "non_null_pct",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def metadata_fields(
    catalog: pd.DataFrame,
) -> list[str]:
    """
    Return the metadata fields available in a catalog.

    Parameters
    ----------
    catalog
        Metadata catalog.

    Returns
    -------
    list[str]
        List of column names.
    """
    return catalog.columns.tolist()


# =============================================================================
# SILVER LAYER — SAVE
# =============================================================================


def save_catalog_to_silver(
    catalog: pd.DataFrame,
    output_path: str | Path | None = None,
) -> Path:
    """
    Normalize and save the metadata catalog as Parquet in the Silver layer.

    Parameters
    ----------
    catalog
        Metadata catalog built by build_metadata_catalog or
        exploration.build_metadata_catalog.
    output_path
        Destination Parquet file. If None, uses the default from config.

    Returns
    -------
    Path
        Path to the saved Parquet file.
    """
    from nlst_lung_cancer.config import SILVER_LUNG_CANCER_CATALOG, SILVER_ROOT

    if output_path is None:
        output_path = SILVER_LUNG_CANCER_CATALOG

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Normalize mixed types for Parquet compatibility
    catalog = normalize_catalog_for_parquet(catalog)

    catalog.to_parquet(output_path, index=False)

    print(f"Catalog saved to {output_path}")
    print(f"  Rows: {len(catalog)}")
    print(f"  Columns: {len(catalog.columns)}")

    return output_path