SELECT p.slide_id, p.cancer_type, m.patient_id
            FROM pathology p
            JOIN masterfile m ON p.slide_id = m.slide_id
            WHERE p.cancer_type = '2-1-Adenocarcinoma'