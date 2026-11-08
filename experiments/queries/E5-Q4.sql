SELECT m.patient_id, p.cancer_type, COUNT(*) AS n_dicoms, COUNT(DISTINCT lc.timepoint) AS n_timepoints
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id
            GROUP BY m.patient_id, p.cancer_type