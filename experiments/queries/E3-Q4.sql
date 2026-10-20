SELECT p.slide_id, p.cancer_type, m.patient_id, t.treatment_category
            FROM treatment t
            JOIN masterfile m ON t.patient_id = m.patient_id
            JOIN pathology p ON m.slide_id = p.slide_id