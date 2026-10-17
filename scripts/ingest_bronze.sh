#!/usr/bin/env bash
# ingest_bronze.sh — Copia dados do NLST para a camada Bronze do Data Lake
# Uso: tmux new -s bronze-ingest './scripts/ingest_bronze.sh 2>&1 | tee ingest_bronze.log'

set -euo pipefail

SRC="/nfs/home/lucas_piovani/NLST-Datasets"
DST="/nfs/home/lucas_piovani/NLST-DataLake/datalake/bronze"

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

echo "=============================================="
echo " NLST Bronze Ingestion — cópia completa"
echo " Início: $(timestamp)"
echo "=============================================="
echo ""

# ── 1. Patologia (.SVS) — copia a estrutura inteira ──────────
echo "── PATOLOGIA ──────────────────────────────────"
mkdir -p "$DST/pathology_samples"

rsync -av --progress \
    "$SRC/2-NLST-Pathology-Image-Batches/" \
    "$DST/pathology_samples/"

echo "[$(timestamp)] Patologia concluída ✓"
echo ""

# ── 2. Lung Cancer (DICOM) — Screen Detected ─────────────────
echo "── LUNG CANCER: Screen Detected ─────────────"
mkdir -p "$DST/lung_cancer_samples/screen_detected"

rsync -av --progress \
    "$SRC/3-NLST-Lung-Cancer-Selection-Batches/3-1-Screen-Detected-Lung-Cancers/" \
    "$DST/lung_cancer_samples/screen_detected/"

echo "[$(timestamp)] Screen Detected concluído ✓"
echo ""

# ── 3. Lung Cancer (DICOM) — Other ───────────────────────────
echo "── LUNG CANCER: Other ───────────────────────"
mkdir -p "$DST/lung_cancer_samples/other"

rsync -av --progress \
    "$SRC/3-NLST-Lung-Cancer-Selection-Batches/3-2-Other-Lung-Cancers/" \
    "$DST/lung_cancer_samples/other/"

echo "[$(timestamp)] Other Lung Cancers concluído ✓"
echo ""

# ── Resumo ────────────────────────────────────────────────────
echo "=============================================="
echo " RESUMO — $(timestamp)"
echo "=============================================="
echo ""
echo "Patologia:"
du -sh "$DST/pathology_samples/"
find "$DST/pathology_samples/" -name "*.svs" | wc -l
echo "arquivos .SVS"
echo ""
echo "Lung Cancer:"
du -sh "$DST/lung_cancer_samples/screen_detected/"
du -sh "$DST/lung_cancer_samples/other/"
echo ""
echo "Total Bronze:"
du -sh "$DST"
echo ""
echo "=============================================="
echo " Concluído: $(timestamp)"
echo "=============================================="