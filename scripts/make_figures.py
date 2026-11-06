#!/usr/bin/env python3
"""Gera as figuras do artigo (PDF e PNG) a partir dos resultados dos experimentos."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "results"
OUT = ROOT / "experiments" / "figures" / "artigo"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.bbox": "tight",
                     "savefig.dpi": 300})
C_CLI, C_MOT, C_ALT = "#077A9D", "#FFAB00", "#FF3621"

res = pl.read_parquet(RESULTS / "experiment_results.parquet")
eng = pl.read_csv(RESULTS / "engine_times.csv")
card = pl.read_csv(RESULTS / "cardinality.csv")
df = res.join(eng.select("query_id", "engine_mean_ms", "engine_std_ms"),
              on="query_id", how="left").with_columns(
    (pl.col("mean_time_s") * 1000).alias("cli_ms"),
    (pl.col("std_time_s") * 1000).alias("cli_std"))
R = {r["query_id"]: r for r in df.iter_rows(named=True)}


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}")
    plt.close(fig)
    print("  ", name)


def grouped(ax, ids, x):
    ax.bar(x - 0.2, [R[q]["cli_ms"] for q in ids], 0.4, color=C_CLI,
           label="Medido no cliente")
    ax.bar(x + 0.2, [R[q]["engine_mean_ms"] for q in ids], 0.4, color=C_MOT,
           label="Interno do DuckDB")


# Visão geral: cliente vs. motor
ids = sorted(R)
y = np.arange(len(ids))
fig, ax = plt.subplots(figsize=(6.3, 5.2))
ax.barh(y - 0.2, [R[q]["cli_ms"] for q in ids], 0.4, color=C_CLI, label="Medido no cliente")
ax.barh(y + 0.2, [R[q]["engine_mean_ms"] for q in ids], 0.4, color=C_MOT, label="Interno do DuckDB")
ax.set_yticks(y, ids)
ax.invert_yaxis()
ax.set_xscale("log")
ax.set_xlabel("Tempo médio (ms, escala log)")
ax.legend(frameon=False, loc="lower right")
save(fig, "fig_cliente_vs_motor")

# E1: filtros
e1 = [f"E1-Q{i}" for i in range(1, 8)]
rot = ["Q1\nsem filtro", "Q2\nadenoc.", "Q3\nbronq.", "Q4\nsem filtro",
       "Q5\nscreen-det.", "Q6\nsem filtro", "Q7\ncirúrgico"]
cores = ["#8BCAE7"] * 3 + [C_CLI] * 2 + ["#00A972"] * 2
x = np.arange(7)
fig, ax = plt.subplots(figsize=(6.3, 2.8))
ax.bar(x, [R[q]["cli_ms"] for q in e1], yerr=[R[q]["cli_std"] for q in e1],
       color=cores, capsize=3)
for xi, q in zip(x, e1):
    ax.text(xi, R[q]["cli_ms"] * 1.25, f'{R[q]["row_count"]:,}'.replace(",", "."),
            ha="center", fontsize=7)
ax.set_yscale("log")
ax.set_xticks(x, rot)
ax.set_ylabel("Tempo médio (ms, log)")
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ("#8BCAE7", C_CLI, "#00A972")]
ax.legend(handles, [r"P $\bowtie$ M", r"M $\bowtie$ L", r"Pt $\bowtie$ T"],
          frameon=False, loc="upper left")
save(fig, "fig_e1_filtros")

# E2: tamanho das relações
e2, pct = ["E2-Q1", "E2-Q2", "E2-Q3", "E2-Q4"], [10, 25, 50, 100]
fig, ax = plt.subplots(figsize=(3.2, 2.6))
ax.errorbar(pct, [R[q]["cli_ms"] for q in e2], yerr=[R[q]["cli_std"] for q in e2],
            marker="o", color=C_CLI, capsize=3, label="Cliente")
ax.errorbar(pct, [R[q]["engine_mean_ms"] for q in e2], yerr=[R[q]["engine_std_ms"] for q in e2],
            marker="s", color=C_MOT, capsize=3, label="DuckDB")
ax.set_xticks(pct, [f"{p}%" for p in pct])
ax.set_xlabel("Amostra de lung_cancer")
ax.set_ylabel("Tempo médio (ms)")
ax.legend(frameon=False)
save(fig, "fig_e2_tamanho")

# E3: ordem das junções
pares = [("E3-Q1", "E3-Q2", "P, M, L"), ("E3-Q3", "E3-Q4", "P, M, T"),
         ("E3-Q5", "E3-Q6", "P, M, L, T"), ("E3-Q7", "E3-Q8", "Pt, C, T")]
x = np.arange(4)
fig, ax = plt.subplots(figsize=(6.3, 2.6))
for off, idx, cor, lab in [(-0.2, 0, C_CLI, "Ordem escrita original (Q ímpar)"),
                           (0.2, 1, C_ALT, "Ordem escrita invertida (Q par)")]:
    ax.bar(x + off, [R[p[idx]]["cli_ms"] for p in pares], 0.4,
           yerr=[R[p[idx]]["cli_std"] for p in pares], capsize=3, color=cor, label=lab)
ax.set_yscale("log")
ax.set_xticks(x, [p[2] for p in pares])
ax.set_ylabel("Tempo médio (ms, log)")
ax.legend(frameon=False)
save(fig, "fig_e3_ordem")

# E4: cardinalidade estimada vs. real
j = card.filter(pl.col("is_join") & pl.col("estimated").is_not_null() & (pl.col("actual") > 0))
if j.height:
    lo = min(j["actual"].min(), j["estimated"].min()) * 0.5
    hi = max(j["actual"].max(), j["estimated"].max()) * 2
    fig, ax = plt.subplots(figsize=(3.2, 3.0))
    ax.scatter(j["actual"], j["estimated"], s=18, color=C_CLI, zorder=3)
    ax.plot([lo, hi], [lo, hi], "k-", lw=0.8, label="Estimativa exata")
    ax.plot([lo, hi], [2 * lo, 2 * hi], "k--", lw=0.6, label="q-error = 2")
    ax.plot([lo, hi], [lo / 2, hi / 2], "k--", lw=0.6)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("Cardinalidade real")
    ax.set_ylabel("Cardinalidade estimada")
    ax.legend(frameon=False, fontsize=7)
    save(fig, "fig_e4_cardinalidade")

# E5: agregação
e5 = ["E3-Q1", "E5-Q1", "E5-Q2", "E5-Q3", "E5-Q4"]
rot = ["E3-Q1\n(sem agreg.)", "E5-Q1", "E5-Q2", "E5-Q3\n(agreg. antes)", "E5-Q4\n(agreg. depois)"]
x = np.arange(5)
fig, ax = plt.subplots(figsize=(6.3, 2.6))
grouped(ax, e5, x)
ax.set_yscale("log")
ax.set_xticks(x, rot)
ax.set_ylabel("Tempo médio (ms, log)")
ax.legend(frameon=False)
save(fig, "fig_e5_agregacao")