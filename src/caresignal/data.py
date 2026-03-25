from __future__ import annotations

import numpy as np
import pandas as pd


DIAGNOSIS_CATEGORIES = [
    "Cardiac",
    "Respiratory",
    "Diabetes",
    "Oncology",
    "Neurological",
    "Other",
]
DIAGNOSIS_PROBABILITIES = [0.22, 0.18, 0.20, 0.15, 0.12, 0.13]


def generate_synthetic_patients(n_rows: int = 2000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    age = rng.normal(loc=60, scale=15, size=n_rows).clip(18, 90).astype(int)
    gender = rng.integers(0, 2, size=n_rows)
    num_prior_admissions = rng.negative_binomial(n=1, p=0.4, size=n_rows).clip(0, 10)

    chronic_lambda = np.clip((age - 18) / 24, 0, None)
    num_chronic_conditions = rng.poisson(lam=chronic_lambda).clip(0, 8).astype(int)

    primary_diagnosis_category = rng.choice(
        DIAGNOSIS_CATEGORIES,
        size=n_rows,
        p=DIAGNOSIS_PROBABILITIES,
    )

    base_meds = num_chronic_conditions * 2 + rng.poisson(lam=2, size=n_rows)
    num_medications = base_meds.clip(0, 20).astype(int)

    linear_pred = (
        0.015 * (age - 18)
        + 0.20 * num_prior_admissions
        + 0.22 * num_chronic_conditions
        + 0.05 * num_medications
        + np.where(primary_diagnosis_category == "Cardiac", 0.35, 0)
        + np.where(primary_diagnosis_category == "Oncology", 0.45, 0)
        + np.where(primary_diagnosis_category == "Respiratory", 0.15, 0)
        + np.where(primary_diagnosis_category == "Diabetes", 0.10, 0)
        + np.where(primary_diagnosis_category == "Neurological", 0.05, 0)
    )

    target_rate = 0.30
    intercepts = np.linspace(-10, 5, 5000)
    rates = np.array([
        np.mean(1 / (1 + np.exp(-(b + linear_pred)))) for b in intercepts
    ])
    best_intercept = intercepts[np.argmin(np.abs(rates - target_rate))]

    log_odds = best_intercept + linear_pred
    readmit_prob = 1 / (1 + np.exp(-log_odds))
    readmitted_30d = (rng.uniform(size=n_rows) < readmit_prob).astype(int)

    patient_df = pd.DataFrame(
        {
            "age": age,
            "gender": gender,
            "num_prior_admissions": num_prior_admissions,
            "num_chronic_conditions": num_chronic_conditions,
            "primary_diagnosis_category": primary_diagnosis_category,
            "num_medications": num_medications,
            "readmitted_30d": readmitted_30d,
        }
    )

    readmit_rate = patient_df["readmitted_30d"].mean()
    if patient_df.shape != (n_rows, 7):
        raise ValueError("Unexpected patient dataframe shape")
    if patient_df.isnull().sum().sum() != 0:
        raise ValueError("Synthetic dataset contains nulls")
    if not 0.25 <= readmit_rate <= 0.35:
        raise ValueError(f"Class balance out of range: {readmit_rate:.2%}")

    return patient_df
