#!/usr/bin/env python3
"""Build the pathology metadata catalog (Bronze → Silver)."""

import sys
from pathlib import Path

# Garantir que src/ está no path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import polars as pl

from nlst_pathology.config import PATHOLOGY_ROOT, SILVER_PATHOLOGY_CATALOG
from nlst_pathology.discovery import list_cancer_types, list_batches, get_batch
from nlst_pathology.catalog import build_metadata_catalog, save_catalog_to_silver


def main() -> None:
    print("=" * 60)
    print("BUILD SILVER — Pathology Metadata Catalog")
    print("=" * 60)

    # 1. Listar batches disponíveis na Bronze
    print(f"\nSource: {PATHOLOGY_ROOT}")
    print(f"Cancer types: {list_cancer_types()}")

    batch_names = list_batches()
    print(f"Batches: {batch_names}")

    # 2. Construir catálogo completo
    batches = [get_batch(b) for b in batch_names]
    print(f"\nProcessando {len(batches)} batches...")

    catalog = build_metadata_catalog(batches)
    print(f"\nCatálogo: {catalog.shape[0]} slides × {catalog.shape[1]} colunas")
    print(catalog.head())

    # 3. Salvar na Silver
    save_catalog_to_silver(catalog)

    # 4. Validar leitura
    print("\n── Validação ──")
    df = pl.read_parquet(SILVER_PATHOLOGY_CATALOG)
    print(f"Silver pathology: {df.shape[0]} rows × {df.shape[1]} cols")
    print(df.schema)

    print("\n✓ Done!")


if __name__ == "__main__":
    main()