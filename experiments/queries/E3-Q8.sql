SELECT pt.patient_id, pt.age, cod.icd10_code, t.treatment_category
            FROM treatment t
            JOIN cause_of_death cod ON t.patient_id = cod.patient_id
            JOIN participant pt ON t.patient_id = pt.patient_id