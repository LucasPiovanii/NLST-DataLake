"""Extração de metadados de arquivos DICOM para a camada Silver."""

from pathlib import Path

import polars as pl
import pydicom

from nlst_datalake.config import LUNG_CANCER_ROOT


def _safe_get(ds: pydicom.Dataset, keyword: str, default=None):
    """Extrai um valor do dataset DICOM de forma segura."""
    elem = ds.get(keyword)
    if elem is None:
        return default
    val = elem.value
    if val == "":
        return default
    return val


def _try_float(value) -> float | None:
    """Tenta converter para float, retorna None se falhar."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def extract_single_dicom(dcm_path: Path) -> dict:
    """Extrai metadados de um único arquivo DICOM."""
    rel = dcm_path.relative_to(LUNG_CANCER_ROOT)
    parts = rel.parts

    # Identificar campos pela estrutura de pastas
    pid = None
    timepoint = None
    cancer_category = parts[0] if len(parts) >= 1 else "unknown"

    for p in parts:
        if p.startswith("T") and len(p) == 2 and p[1].isdigit():
            timepoint = p
        elif p.isdigit() and len(p) >= 5:
            pid = p

    record = {
        "pid": pid,
        "timepoint": timepoint,
        "cancer_category": cancer_category,
        "source_file": str(dcm_path),
        "file_size_kb": round(dcm_path.stat().st_size / 1024, 2),
    }

    try:
        ds = pydicom.dcmread(str(dcm_path), stop_before_pixels=True)
        record.update({
            "patient_id_dicom": _safe_get(ds, "PatientID"),
            "patient_sex": _safe_get(ds, "PatientSex"),
            "patient_age": _safe_get(ds, "PatientAge"),
            "study_date": _safe_get(ds, "StudyDate"),
            "study_description": _safe_get(ds, "StudyDescription"),
            "modality": _safe_get(ds, "Modality"),
            "series_uid": _safe_get(ds, "SeriesInstanceUID"),
            "sop_instance_uid": _safe_get(ds, "SOPInstanceUID"),
            "series_description": _safe_get(ds, "SeriesDescription"),
            "series_number": _safe_get(ds, "SeriesNumber"),
            "slice_thickness": _try_float(_safe_get(ds, "SliceThickness")),
            "pixel_spacing": str(_safe_get(ds, "PixelSpacing")),
            "kvp": _try_float(_safe_get(ds, "KVP")),
            "rows": _safe_get(ds, "Rows"),
            "columns": _safe_get(ds, "Columns"),
            "reconstruction_diameter": _try_float(
                _safe_get(ds, "ReconstructionDiameter")
            ),
        })
    except Exception as e:
        record["extraction_error"] = str(e)

    return record


def extract_dicom_metadata(dicom_files: list[Path]) -> pl.DataFrame:
    """Extrai metadados de uma lista de arquivos DICOM."""
    records = [extract_single_dicom(f) for f in dicom_files]
    return pl.DataFrame(records)