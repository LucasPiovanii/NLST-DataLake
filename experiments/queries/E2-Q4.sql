SELECT m.patient_id, lc.modality
            FROM masterfile m
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id