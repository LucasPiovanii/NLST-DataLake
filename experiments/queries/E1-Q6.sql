SELECT pt.patient_id, pt.age, pt.gender, t.treatment_category
            FROM participant pt
            JOIN treatment t ON pt.patient_id = t.patient_id