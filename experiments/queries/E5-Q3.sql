SELECT m.patient_id, p.cancer_type, lc_agg.n_dicoms, lc_agg.n_timepoints
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            JOIN (
                SELECT patient_id, COUNT(*) AS n_dicoms, COUNT(DISTINCT timepoint) AS n_timepoints
                FROM lung_cancer
                GROUP BY patient_id
            ) lc_agg ON m.patient_id = lc_agg.patient_id