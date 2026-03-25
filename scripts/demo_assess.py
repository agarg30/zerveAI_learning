from caresignal.inference import assess_patient


def main() -> None:
    patients = [
        {
            "age": 28,
            "gender": "F",
            "prior_admissions": 0,
            "chronic_conditions": 1,
            "primary_diagnosis": "Respiratory",
            "medications": 2,
        },
        {
            "age": 82,
            "gender": "M",
            "prior_admissions": 5,
            "chronic_conditions": 6,
            "primary_diagnosis": "Cardiac",
            "medications": 12,
        },
    ]

    for patient in patients:
        print(assess_patient(**patient))


if __name__ == "__main__":
    main()
