SELECT p.cancer_type, COUNT(*) AS n_records
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id
            GROUP BY p.cancer_type