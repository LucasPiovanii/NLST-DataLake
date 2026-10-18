#!/usr/bin/env python3
"""Build Gold layer: clean, type, and standardize Silver tables for DuckDB experiments."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import polars as pl

SILVER = PROJECT_ROOT / "datalake" / "silver"
GOLD = PROJECT_ROOT / "datalake" / "gold"


def build_gold_pathology() -> pl.DataFrame:
    """Silver → Gold: Pathology slides metadata."""
    print("\n── 1. Pathology ──")

    df = pl.read_parquet(SILVER / "pathology_metadata.parquet")
    print(f"  Silver: {df.shape[0]} rows × {df.shape[1]} cols")

    gold = df.select([
        # Identificação
        pl.col("slide_id"),
        pl.col("cancer_type"),
        pl.col("batch"),
        pl.col("filename"),

        # Dimensões da imagem
        pl.col("width"),
        pl.col("height"),
        pl.col("level_count"),

        # Tamanho do arquivo
        pl.col("file_size_bytes"),
        pl.col("file_size_mb"),

        # Scanner / aquisição
        pl.col("openslide.vendor").alias("vendor"),
        pl.col("openslide.mpp-x").cast(pl.Float64, strict=False).alias("mpp_x"),
        pl.col("openslide.mpp-y").cast(pl.Float64, strict=False).alias("mpp_y"),
        pl.col("openslide.objective-power").cast(pl.Float64, strict=False).alias("objective_power"),

        # Aperio metadata
        pl.col("aperio.AppMag").alias("aperio_app_mag"),
        pl.col("aperio.Date").alias("aperio_scan_date"),
        pl.col("aperio.MPP").cast(pl.Float64, strict=False).alias("aperio_mpp"),
        pl.col("aperio.ScanScope ID").alias("aperio_scanscope_id"),

        # Pyramid levels (level 0 = full resolution)
        pl.col("openslide.level[0].width").cast(pl.Int64, strict=False).alias("level0_width"),
        pl.col("openslide.level[0].height").cast(pl.Int64, strict=False).alias("level0_height"),
        pl.col("openslide.level[0].tile-width").cast(pl.Int64, strict=False).alias("level0_tile_width"),
        pl.col("openslide.level[0].tile-height").cast(pl.Int64, strict=False).alias("level0_tile_height"),
    ])

    return gold


def build_gold_masterfile() -> pl.DataFrame:
    """Silver → Gold: Masterfile (slide ↔ patient linkage + annotations)."""
    print("\n── 2. Masterfile ──")

    df = pl.read_parquet(SILVER / "masterfile.parquet")
    print(f"  Silver: {df.shape[0]} rows × {df.shape[1]} cols")

    gold = df.select([
        # Chaves de JOIN
        pl.col("pid").cast(pl.Int64, strict=False).cast(pl.Utf8).alias("patient_id"),
        pl.col("image_filename").str.replace(r"\.svs$", "").alias("slide_id"),
        pl.col("image_filename"),

        # Informações do caso
        pl.col("lc_order").cast(pl.Int64, strict=False),
        pl.col("image_filesize").cast(pl.Int64, strict=False),
        pl.col("selected_path").cast(pl.Int64, strict=False),
        pl.col("selected_path_batch").cast(pl.Int64, strict=False),

        # Anotações do bloco
        pl.col("block_annotated").cast(pl.Int64, strict=False),
        pl.col("block_worst_class").cast(pl.Utf8, strict=False),
        pl.col("block_worst_grade"),
        pl.col("block_worst_grade_qual"),
        pl.col("block_slide_cnt"),

        # ROI — contagem e classificações principais
        pl.col("roi_count"),
        pl.col("roi_WHO_class1").cast(pl.Utf8, strict=False),
        pl.col("roi_WHO_class2").cast(pl.Utf8, strict=False),
        pl.col("roi_histology_cat1").cast(pl.Utf8, strict=False),
        pl.col("roi_histology_cat2").cast(pl.Utf8, strict=False),
        pl.col("roi_histology_subtype1").cast(pl.Utf8, strict=False),
        pl.col("roi_histology_subtype2").cast(pl.Utf8, strict=False),

        # ROI — graus
        pl.col("roi_highest_grade1"),
        pl.col("roi_highest_grade2"),
        pl.col("roi_highest_grade_qual1"),
        pl.col("roi_highest_grade_qual2"),

        # ROI — dimensões tumorais
        pl.col("roi_inv_tumor_dim1"),
        pl.col("roi_inv_tumor_dim2"),
        pl.col("roi_tumor_cell_percent1"),
        pl.col("roi_inflamm_cell_percent1"),

        # ROI — invasão
        pl.col("roi_lymph_inv1"),
        pl.col("roi_vessel_inv1"),
        pl.col("roi_likely_met1"),
        pl.col("roi_metastases1"),

        # ROI — morfologia WHO
        pl.col("roi_who_class_beh1"),
        pl.col("roi_who_class_mor1"),
    ])

    return gold


def build_gold_lung_cancer() -> pl.DataFrame:
    """Silver → Gold: Lung cancer DICOM metadata."""
    print("\n── 3. Lung Cancer ──")

    df = pl.read_parquet(SILVER / "lung_cancer_metadata.parquet")
    print(f"  Silver: {df.shape[0]} rows × {df.shape[1]} cols")

    gold = df.select([
        # Chaves de JOIN e identificação
        pl.col("patient_id"),
        pl.col("cancer_category"),
        pl.col("batch"),
        pl.col("sub_batch"),
        pl.col("timepoint"),
        pl.col("filename"),

        # IDs DICOM
        pl.col("PatientID").alias("patient_id_dicom"),
        pl.col("StudyInstanceUID").alias("study_uid"),
        pl.col("SeriesInstanceUID").alias("series_uid"),
        pl.col("SOPInstanceUID").alias("sop_uid"),
        pl.col("series_uid_from_path"),

        # Paciente
        pl.col("PatientSex").alias("patient_sex"),

        # Estudo
        pl.col("StudyDate").alias("study_date"),
        pl.col("StudyDescription").alias("study_description"),
        pl.col("Modality").alias("modality"),

        # Série
        pl.col("SeriesDescription").alias("series_description"),
        pl.col("SeriesNumber").cast(pl.Int64, strict=False).alias("series_number"),

        # Aquisição
        pl.col("SliceThickness").cast(pl.Float64, strict=False).alias("slice_thickness"),
        pl.col("KVP").cast(pl.Float64, strict=False).alias("kvp"),
        pl.col("Exposure").cast(pl.Float64, strict=False).alias("exposure"),
        pl.col("XRayTubeCurrent").cast(pl.Float64, strict=False).alias("xray_tube_current"),
        pl.col("ConvolutionKernel").alias("convolution_kernel"),
        pl.col("ReconstructionDiameter").cast(pl.Float64, strict=False).alias("reconstruction_diameter"),
        pl.col("DataCollectionDiameter").cast(pl.Float64, strict=False).alias("data_collection_diameter"),

        # Imagem
        pl.col("Rows").cast(pl.Int64, strict=False).alias("rows"),
        pl.col("Columns").cast(pl.Int64, strict=False).alias("columns_img"),
        pl.col("PixelSpacing").alias("pixel_spacing"),
        pl.col("BitsAllocated").cast(pl.Int64, strict=False).alias("bits_allocated"),
        pl.col("BitsStored").cast(pl.Int64, strict=False).alias("bits_stored"),
        pl.col("RescaleIntercept").cast(pl.Float64, strict=False).alias("rescale_intercept"),
        pl.col("RescaleSlope").cast(pl.Float64, strict=False).alias("rescale_slope"),

        # Equipamento
        pl.col("Manufacturer").alias("manufacturer"),
        pl.col("ManufacturerModelName").alias("manufacturer_model"),
        pl.col("SoftwareVersions").alias("software_versions"),

        # Posição
        pl.col("SliceLocation").cast(pl.Float64, strict=False).alias("slice_location"),
        pl.col("InstanceNumber").cast(pl.Int64, strict=False).alias("instance_number"),
        pl.col("BodyPartExamined").alias("body_part"),
    ])

    return gold


def validate_join_keys(
    pathology: pl.DataFrame,
    masterfile: pl.DataFrame,
    lung_cancer: pl.DataFrame,
) -> None:
    """Validate JOIN key overlap between Gold tables."""
    print("\n── 4. Validação de Chaves de JOIN ──")

    path_ids = set(pathology["slide_id"].to_list())
    mf_slide_ids = set(masterfile["slide_id"].to_list())
    mf_pids = set(masterfile["patient_id"].drop_nulls().to_list())
    lc_pids = set(lung_cancer["patient_id"].drop_nulls().to_list())

    print(f"\n  Pathology slides:              {len(path_ids)}")
    print(f"  Masterfile slides:             {len(mf_slide_ids)}")
    print(f"  Pathology ∩ Masterfile:        {len(path_ids & mf_slide_ids)}")

    print(f"\n  Masterfile patients:           {len(mf_pids)}")
    print(f"  Lung Cancer patients:          {len(lc_pids)}")
    print(f"  Masterfile ∩ Lung Cancer:      {len(mf_pids & lc_pids)}")

    # Pacientes presentes nas 3 tabelas
    mf_with_path = masterfile.filter(pl.col("slide_id").is_in(list(path_ids)))
    pids_in_all_3 = set(mf_with_path["patient_id"].drop_nulls().to_list()) & lc_pids
    print(f"\n  Pacientes nas 3 tabelas:       {len(pids_in_all_3)}")


def main() -> None:
    print("=" * 60)
    print("BUILD GOLD LAYER")
    print("=" * 60)

    GOLD.mkdir(parents=True, exist_ok=True)

    # Build
    gold_pathology = build_gold_pathology()
    gold_masterfile = build_gold_masterfile()
    gold_lung_cancer = build_gold_lung_cancer()

    # Save
    for name, df in [
        ("pathology", gold_pathology),
        ("masterfile", gold_masterfile),
        ("lung_cancer", gold_lung_cancer),
    ]:
        path = GOLD / f"{name}.parquet"
        df.write_parquet(path)
        print(f"  → {name}: {df.shape[0]} rows × {df.shape[1]} cols → {path.name}")

    # Validate
    validate_join_keys(gold_pathology, gold_masterfile, gold_lung_cancer)

    # Summary
    print("\n" + "=" * 60)
    print("RESUMO GOLD LAYER")
    print("=" * 60)
    total_bytes = sum(f.stat().st_size for f in GOLD.glob("*.parquet"))
    print(f"  pathology.parquet:    {gold_pathology.shape}")
    print(f"  masterfile.parquet:   {gold_masterfile.shape}")
    print(f"  lung_cancer.parquet:  {gold_lung_cancer.shape}")
    print(f"  Total size:           {total_bytes / (1024**2):.1f} MB")
    print("\n✓ Done!")


if __name__ == "__main__":
    main()