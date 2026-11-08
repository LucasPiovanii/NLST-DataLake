SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id