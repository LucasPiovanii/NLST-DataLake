SELECT m.patient_id, lc.modality
            FROM masterfile m
            JOIN (SELECT * FROM lung_cancer USING SAMPLE 10 PERCENT (bernoulli)) lc
              ON m.patient_id = lc.patient_id