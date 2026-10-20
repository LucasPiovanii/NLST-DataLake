SELECT t.treatment_category, COUNT(DISTINCT m.patient_id) AS n_patients
            FROM masterfile m
            JOIN pathology p ON m.slide_id = p.slide_id
            JOIN treatment t ON m.patient_id = t.patient_id
            GROUP BY t.treatment_category