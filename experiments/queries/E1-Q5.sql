SELECT m.patient_id, m.slide_id, lc.modality, lc.timepoint
            FROM masterfile m
            JOIN lung_cancer lc ON m.patient_id = lc.patient_id
            WHERE lc.cancer_category = 'screen_detected'