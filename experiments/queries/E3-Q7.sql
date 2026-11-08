SELECT pt.patient_id, pt.age, cod.icd10_code, t.treatment_category
            FROM participant pt
            JOIN cause_of_death cod ON pt.patient_id = cod.patient_id
            JOIN treatment t ON pt.patient_id = t.patient_id