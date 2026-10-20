SELECT p.slide_id, p.cancer_type, m.patient_id, lc.modality, t.treatment_category
            FROM lung_cancer lc
            JOIN treatment t ON lc.patient_id = t.patient_id
            JOIN masterfile m ON lc.patient_id = m.patient_id
            JOIN pathology p ON m.slide_id = p.slide_id