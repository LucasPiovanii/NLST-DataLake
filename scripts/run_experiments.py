#!/usr/bin/env python3
"""
Run all JOIN optimization experiments and save results.

Collects: execution time (10 rounds), EXPLAIN plan, EXPLAIN ANALYZE plan,
row counts, and algorithm choices for each query.

Results are saved to experiments/results/ as Parquet and JSON.
"""

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import duckdb
import polars as pl

DUCKDB_PATH = PROJECT_ROOT / "datalake" / "nlst.duckdb"
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"
PLANS_DIR = PROJECT_ROOT / "experiments" / "plans"
QUERIES_DIR = PROJECT_ROOT / "experiments" / "queries"

N_ROUNDS = 10


# ─────────────────────────────────────────────────────────────
# Query Definitions
# ─────────────────────────────────────────────────────────────

EXPERIMENTS = {
    # ── Experiment 1: Filter vs No Filter ─────────────────────
    "E1-Q1": {
        "experiment": "E1_filter_vs_no_filter",
        "description": "JOIN pathology-masterfile, no filter (baseline)",
        "sql": """
            SELECT p.slide_id, p.cancer_type, m.patient_id
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
        """,
    },
    "E1-Q2": {
        "experiment": "E1_filter_vs_no_filter",
        "description": "JOIN pathology-masterfile, filter adenocarcinoma (~45%)",
        "sql": """
            SELECT p.slide_id, p.cancer_type, m.patient_id
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            WHERE p.cancer_type = '2-1-Adenocarcinoma'
        """,
    },
    "E1-Q3": {
        "experiment": "E1_filter_vs_no_filter",
        "description": "JOIN pathology-masterfile, filter bronchio-alveolar (~5%)",
        "sql": """
            SELECT p.slide_id, p.cancer_type, m.patient_id
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            WHERE p.cancer_type = '2-3-Bronchio-Alveolar-Carcinoma'
        """,
    },
    "E1-Q4": {
        "experiment": "E1_filter_vs_no_filter",
        "description": "JOIN masterfile-lung_cancer, no filter (baseline with cardinality explosion)",
        "sql": """
            SELECT m.patient_id, m.slide_id, lc.modality, lc.timepoint
            FROM masterfile m
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id
        """,
    },
    "E1-Q5": {
        "experiment": "E1_filter_vs_no_filter",
        "description": "JOIN masterfile-lung_cancer, filter screen_detected",
        "sql": """
            SELECT m.patient_id, m.slide_id, lc.modality, lc.timepoint
            FROM masterfile m
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id
            WHERE lc.cancer_category = 'screen_detected'
        """,
    },
    "E1-Q6": {
        "experiment": "E1_filter_vs_no_filter",
        "description": "JOIN participant-treatment, no filter",
        "sql": """
            SELECT pt.patient_id, pt.age, pt.gender, t.treatment_category
            FROM participant pt
            JOIN treatment t ON pt.patient_id = t.patient_id
        """,
    },
    "E1-Q7": {
        "experiment": "E1_filter_vs_no_filter",
        "description": "JOIN participant-treatment, filter surgical only",
        "sql": """
            SELECT pt.patient_id, pt.age, pt.gender, t.treatment_category
            FROM participant pt
            JOIN treatment t ON pt.patient_id = t.patient_id
            WHERE t.treatment_category = '(2) Surgical'
        """,
    },

    # ── Experiment 2: Data Size Variation ─────────────────────
    "E2-Q1": {
        "experiment": "E2_data_size",
        "description": "lung_cancer 10% sample JOIN masterfile",
        "sql": """
            SELECT m.patient_id, lc.modality
            FROM masterfile m
            JOIN (SELECT * FROM lung_cancer USING SAMPLE 10 PERCENT (bernoulli)) lc
              ON m.patient_id = lc.patient_id
        """,
    },
    "E2-Q2": {
        "experiment": "E2_data_size",
        "description": "lung_cancer 25% sample JOIN masterfile",
        "sql": """
            SELECT m.patient_id, lc.modality
            FROM masterfile m
            JOIN (SELECT * FROM lung_cancer USING SAMPLE 25 PERCENT (bernoulli)) lc
              ON m.patient_id = lc.patient_id
        """,
    },
    "E2-Q3": {
        "experiment": "E2_data_size",
        "description": "lung_cancer 50% sample JOIN masterfile",
        "sql": """
            SELECT m.patient_id, lc.modality
            FROM masterfile m
            JOIN (SELECT * FROM lung_cancer USING SAMPLE 50 PERCENT (bernoulli)) lc
              ON m.patient_id = lc.patient_id
        """,
    },
    "E2-Q4": {
        "experiment": "E2_data_size",
        "description": "lung_cancer 100% JOIN masterfile",
        "sql": """
            SELECT m.patient_id, lc.modality
            FROM masterfile m
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id
        """,
    },

    # ── Experiment 3: JOIN Order ──────────────────────────────
    "E3-Q1": {
        "experiment": "E3_join_order",
        "description": "3-way: pathology -> masterfile -> lung_cancer (small first)",
        "sql": """
            SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id
        """,
    },
    "E3-Q2": {
        "experiment": "E3_join_order",
        "description": "3-way: lung_cancer -> masterfile -> pathology (large first)",
        "sql": """
            SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality
            FROM lung_cancer lc
            JOIN masterfile m ON lc.patient_id = m.patient_id
            JOIN pathology p ON m.slide_id = p.slide_id
        """,
    },
    "E3-Q3": {
        "experiment": "E3_join_order",
        "description": "3-way: pathology -> masterfile -> treatment (small-small-medium)",
        "sql": """
            SELECT p.slide_id, p.cancer_type, m.patient_id, t.treatment_category
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            JOIN treatment t ON m.patient_id = t.patient_id
        """,
    },
    "E3-Q4": {
        "experiment": "E3_join_order",
        "description": "3-way: treatment -> masterfile -> pathology (medium first)",
        "sql": """
            SELECT p.slide_id, p.cancer_type, m.patient_id, t.treatment_category
            FROM treatment t
            JOIN masterfile m ON t.patient_id = m.patient_id
            JOIN pathology p ON m.slide_id = p.slide_id
        """,
    },
    "E3-Q5": {
        "experiment": "E3_join_order",
        "description": "4-way: pathology -> masterfile -> lung_cancer -> treatment",
        "sql": """
            SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality, t.treatment_category
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id
            JOIN treatment t ON m.patient_id = t.patient_id
        """,
    },
    "E3-Q6": {
        "experiment": "E3_join_order",
        "description": "4-way: lung_cancer -> treatment -> masterfile -> pathology (large first)",
        "sql": """
            SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality, t.treatment_category
            FROM lung_cancer lc
            JOIN treatment t ON lc.patient_id = t.patient_id
            JOIN masterfile m ON lc.patient_id = m.patient_id
            JOIN pathology p ON m.slide_id = p.slide_id
        """,
    },
    "E3-Q7": {
        "experiment": "E3_join_order",
        "description": "3-way: participant -> cause_of_death -> treatment",
        "sql": """
            SELECT pt.patient_id, pt.age, cod.icd10_code, t.treatment_category
            FROM participant pt
            JOIN cause_of_death cod ON pt.patient_id = cod.patient_id
            JOIN treatment t ON pt.patient_id = t.patient_id
        """,
    },
    "E3-Q8": {
        "experiment": "E3_join_order",
        "description": "3-way: treatment -> cause_of_death -> participant (reversed)",
        "sql": """
            SELECT pt.patient_id, pt.age, cod.icd10_code, t.treatment_category
            FROM treatment t
            JOIN cause_of_death cod ON t.patient_id = cod.patient_id
            JOIN participant pt ON t.patient_id = pt.patient_id
        """,
    },

    # ── Experiment 5: JOIN + Aggregation ──────────────────────
    "E5-Q1": {
        "experiment": "E5_join_aggregation",
        "description": "COUNT by cancer_type after 3-way join",
        "sql": """
            SELECT p.cancer_type, COUNT(*) AS n_records
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id
            GROUP BY p.cancer_type
        """,
    },
    "E5-Q2": {
        "experiment": "E5_join_aggregation",
        "description": "COUNT DISTINCT patients by treatment_category after 3-way join",
        "sql": """
            SELECT t.treatment_category, COUNT(DISTINCT m.patient_id) AS n_patients
            FROM masterfile m
            JOIN pathology p ON m.slide_id = p.slide_id
            JOIN treatment t ON m.patient_id = t.patient_id
            GROUP BY t.treatment_category
        """,
    },
    "E5-Q3": {
        "experiment": "E5_join_aggregation",
        "description": "Aggregation BEFORE join (subquery pre-aggregates lung_cancer)",
        "sql": """
            SELECT m.patient_id, p.cancer_type, lc_agg.n_dicoms, lc_agg.n_timepoints
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            JOIN (
                SELECT patient_id, COUNT(*) AS n_dicoms, COUNT(DISTINCT timepoint) AS n_timepoints
                FROM lung_cancer
                GROUP BY patient_id
            ) lc_agg ON m.patient_id = lc_agg.patient_id
        """,
    },
    "E5-Q4": {
        "experiment": "E5_join_aggregation",
        "description": "Aggregation AFTER join (aggregate on full join result)",
        "sql": """
            SELECT m.patient_id, p.cancer_type, COUNT(*) AS n_dicoms, COUNT(DISTINCT lc.timepoint) AS n_timepoints
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id
            GROUP BY m.patient_id, p.cancer_type
        """,
    },
}


# ─────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────


def run_experiments() -> None:
    print("=" * 70)
    print(f"NLST JOIN OPTIMIZATION EXPERIMENTS — {len(EXPERIMENTS)} queries × {N_ROUNDS} rounds")
    print("=" * 70)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    QUERIES_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    all_results = []

    for query_id, spec in EXPERIMENTS.items():
        sql = spec["sql"].strip()
        desc = spec["description"]
        experiment = spec["experiment"]

        print(f"\n{'─' * 70}")
        print(f"  {query_id}: {desc}")
        print(f"  Experiment: {experiment}")

        # Save query SQL
        (QUERIES_DIR / f"{query_id}.sql").write_text(sql)

        # 1. Row count
        count_sql = f"SELECT COUNT(*) FROM ({sql}) AS _q"
        try:
            row_count = con.sql(count_sql).fetchone()[0]
        except Exception as e:
            print(f"  ❌ COUNT failed: {e}")
            row_count = -1
        print(f"  Rows: {row_count:,}")

        # 2. EXPLAIN (estimated plan)
        try:
            explain_rows = con.sql(f"EXPLAIN {sql}").fetchall()
            explain_text = "\n".join(row[1] for row in explain_rows)
            (PLANS_DIR / f"{query_id}_explain.txt").write_text(explain_text)
        except Exception as e:
            explain_text = f"ERROR: {e}"
            print(f"  ❌ EXPLAIN failed: {e}")

        # 3. EXPLAIN ANALYZE (real plan)
        try:
            analyze_rows = con.sql(f"EXPLAIN ANALYZE {sql}").fetchall()
            analyze_text = "\n".join(row[1] for row in analyze_rows)
            (PLANS_DIR / f"{query_id}_explain_analyze.txt").write_text(analyze_text)
        except Exception as e:
            analyze_text = f"ERROR: {e}"
            print(f"  ❌ EXPLAIN ANALYZE failed: {e}")

        # 4. Timing (N rounds)
        times = []
        for i in range(N_ROUNDS):
            start = time.perf_counter()
            con.sql(sql).fetchall()
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        mean_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        std_time = (sum((t - mean_time) ** 2 for t in times) / len(times)) ** 0.5

        print(f"  Time: {mean_time:.4f}s (min={min_time:.4f}, max={max_time:.4f}, std={std_time:.4f})")

        # Collect result
        all_results.append({
            "query_id": query_id,
            "experiment": experiment,
            "description": desc,
            "row_count": row_count,
            "mean_time_s": round(mean_time, 6),
            "min_time_s": round(min_time, 6),
            "max_time_s": round(max_time, 6),
            "std_time_s": round(std_time, 6),
            "times": [round(t, 6) for t in times],
        })

    con.close()

    # Save all results
    print(f"\n{'=' * 70}")
    print("SAVING RESULTS")
    print(f"{'=' * 70}")

    # As Parquet (for analysis)
    df_results = pl.DataFrame([
        {k: v for k, v in r.items() if k != "times"}
        for r in all_results
    ])
    df_results.write_parquet(RESULTS_DIR / "experiment_results.parquet")
    print(f"  Parquet: {RESULTS_DIR / 'experiment_results.parquet'}")

    # As JSON (with full timing arrays)
    with open(RESULTS_DIR / "experiment_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"  JSON: {RESULTS_DIR / 'experiment_results.json'}")

    # Summary table
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(df_results.select([
        "query_id", "experiment", "row_count", "mean_time_s", "min_time_s", "max_time_s"
    ]))

    print(f"\n  Plans saved to: {PLANS_DIR}/")
    print(f"  Queries saved to: {QUERIES_DIR}/")
    print(f"\n✓ Done!")


if __name__ == "__main__":
    run_experiments()