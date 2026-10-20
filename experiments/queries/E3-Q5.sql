SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality, t.treatment_category
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id
            JOIN treatment t ON m.patient_id = t.patient_id