from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from caresignal.features import driver_label, engineer_single_patient
from caresignal.train import MODEL_PATH


DEFAULT_SUMMARY = (
    "warranting close post-discharge monitoring and timely outpatient follow-up."
)


@lru_cache(maxsize=1)
def load_bundle(model_path: str | Path = MODEL_PATH) -> dict[str, Any]:
    return joblib.load(model_path)


def generate_clinical_summary(
    age: int,
    gender: str,
    risk_score: float,
    risk_tier: str,
    top_drivers: list[str],
) -> str:
    gender_word = "male" if gender.strip().upper() == "M" else "female"
    d1 = driver_label(top_drivers[0])
    d2 = driver_label(top_drivers[1])
    d3 = driver_label(top_drivers[2])
    return (
        f"This {age}-year-old {gender_word} patient carries a {risk_tier.lower()} 30-day "
        f"readmission risk (score {risk_score:.4f}), driven primarily by {d1} and {d2}. "
        f"Additional concern is noted for {d3}, {DEFAULT_SUMMARY}"
    )


def compute_top_drivers(model: Any, vector: np.ndarray, feature_names: list[str]) -> list[str]:
    try:
        import shap

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(vector)
        values = np.abs(shap_values[0])
        indices = np.argsort(values)[::-1][:3]
        return [feature_names[index] for index in indices]
    except Exception:
        non_zero = np.argsort(np.abs(vector[0]))[::-1][:3]
        return [feature_names[index] for index in non_zero]


def assess_patient(
    age: int,
    gender: str,
    prior_admissions: int,
    chronic_conditions: int,
    primary_diagnosis: str,
    medications: int,
) -> dict[str, Any]:
    bundle = load_bundle()
    model = bundle["model"]
    feature_names = bundle["feature_names"]

    vector, risk_tier = engineer_single_patient(
        age=age,
        gender=gender,
        prior_admissions=prior_admissions,
        chronic_conditions=chronic_conditions,
        primary_diagnosis=primary_diagnosis,
        medications=medications,
        feature_names=feature_names,
    )

    risk_score = round(float(model.predict_proba(vector)[0, 1]), 4)
    top_drivers = compute_top_drivers(model, vector, feature_names)
    summary = generate_clinical_summary(age, gender, risk_score, risk_tier, top_drivers)

    return {
        "patient_input": {
            "age": age,
            "gender": gender,
            "prior_admissions": prior_admissions,
            "chronic_conditions": chronic_conditions,
            "primary_diagnosis": primary_diagnosis,
            "medications": medications,
        },
        "risk_score": risk_score,
        "risk_tier": risk_tier,
        "top_drivers": top_drivers,
        "ai_clinical_summary": summary,
    }
