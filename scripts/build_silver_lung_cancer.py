#!/usr/bin/env python3
"""Build the lung cancer metadata catalog (Bronze → Silver)."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tqdm import tqdm

from nlst_lung_cancer.config import LUNG_CANCER_SOURCES, SILVER_LUNG_CANCER_CATALOG
from nlst_lung_cancer.io import list_files
from nlst_lung_cancer.exploration import build_metadata_catalog
from nlst_lung_cancer.metadata import normalize_catalog_for_parquet, save_catalog_to_silver

import pandas as pd


def main() -> None:
    print("=" * 60)
    print("BUILD SILVER — Lung Cancer Metadata Catalog")
    print("=" * 60)

    all_catalogs = []

    for category, source_path in LUNG_CANCER_SOURCES.items():
        print(f"\n── {category} ──")
        print(f"Source: {source_path}")

        # Listar todos os arquivos DICOM (sem extensão .dcm no NLST)
        files = list_files(source_path, pattern="*", recursive=True)
        print(f"Total files: {len(files)}")

        if not files:
            print("  Nenhum arquivo encontrado, pulando...")
            continue

        # Construir catálogo com barra de progresso
        # Processar em chunks para mostrar progresso
        chunk_size = 500
        records = []

        for i in tqdm(range(0, len(files), chunk_size), desc=f"  {category}", unit="chunk"):
            chunk = files[i : i + chunk_size]
            chunk_catalog = build_metadata_catalog(
                chunk,
                cancer_category=category,
            )
            records.append(chunk_catalog)

        catalog = pd.concat(records, ignore_index=True)
        print(f"  Catalog: {len(catalog)} rows × {len(catalog.columns)} cols")

        all_catalogs.append(catalog)

    # Concatenar tudo
    print("\n── Concatenando catálogos ──")
    full_catalog = pd.concat(all_catalogs, ignore_index=True)
    print(f"Total: {len(full_catalog)} rows × {len(full_catalog.columns)} cols")

    # Salvar na Silver
    save_catalog_to_silver(full_catalog)

    # Validar
    print("\n── Validação ──")
    import polars as pl
    df = pl.read_parquet(SILVER_LUNG_CANCER_CATALOG)
    print(f"Silver lung cancer: {df.shape[0]} rows × {df.shape[1]} cols")

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
