from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from caresignal.data import DIAGNOSIS_CATEGORIES


TIER_BINS = [0, 7.5, 15, 22.5, 30]
TIER_LABELS = ["Low", "Medium", "High", "Critical"]
TIER_MAP = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}

AGE_BINS = [0, 35, 55, 70, 120]
AGE_LABELS = ["Young", "Middle", "Senior", "Elderly"]
AGE_MAP = {"Young": 0, "Middle": 1, "Senior": 2, "Elderly": 3}


@dataclass
class ProcessedData:
    frame: pd.DataFrame
    X: np.ndarray
    y: np.ndarray
    feature_names: list[str]


DRIVER_LABELS = {
    "comorbidity_score": "a high comorbidity burden",
    "age": "advanced age",
    "num_medications": "a high medication count",
    "num_chronic_conditions": "multiple chronic conditions",
    "num_prior_admissions": "frequent prior hospital admissions",
    "admissions_x_conditions": "a high admissions-to-conditions interaction score",
    "age_group": "age-related risk factors",
    "diag_Cardiac": "a primary cardiac diagnosis",
    "diag_Diabetes": "a primary diabetes diagnosis",
    "diag_Respiratory": "a primary respiratory diagnosis",
    "diag_Oncology": "a primary oncology diagnosis",
    "diag_Neurological": "a primary neurological diagnosis",
    "diag_Other": "a complex multi-system diagnosis",
}


def driver_label(feature_name: str) -> str:
    return DRIVER_LABELS.get(feature_name.strip(), feature_name.replace("_", " "))


def _bucket_tier(score: float) -> tuple[int, str]:
    for label, upper in zip(TIER_LABELS, TIER_BINS[1:]):
        if score <= upper:
            return TIER_MAP[label], label
    return 3, "Critical"


def _bucket_age(age: int) -> int:
    for label, upper in zip(AGE_LABELS, AGE_BINS[1:]):
        if age <= upper:
            return AGE_MAP[label]
    return 3


def engineer_single_patient(
    age: int,
    gender: str,
    prior_admissions: int,
    chronic_conditions: int,
    primary_diagnosis: str,
    medications: int,
    feature_names: list[str],
) -> tuple[np.ndarray, str]:
    diagnosis = next(
        (item for item in DIAGNOSIS_CATEGORIES if item.lower() == primary_diagnosis.strip().lower()),
        "Other",
    )
    gender_value = 1 if gender.strip().upper() == "M" else 0
    comorbidity_score = min(chronic_conditions * 1.5 + prior_admissions * 1.2 + medications * 0.5, 30)
    risk_tier, risk_label = _bucket_tier(comorbidity_score)
    age_group = _bucket_age(age)
    diag_values = {f"diag_{name}": float(name == diagnosis) for name in DIAGNOSIS_CATEGORIES}

    row = {
        "age": float(age),
        "gender": float(gender_value),
        "num_prior_admissions": float(prior_admissions),
        "num_chronic_conditions": float(chronic_conditions),
        "num_medications": float(medications),
        **diag_values,
        "comorbidity_score": float(comorbidity_score),
        "risk_tier": float(risk_tier),
        "age_group": float(age_group),
        "admissions_x_conditions": float(prior_admissions * chronic_conditions),
    }
    vector = np.array([[row[name] for name in feature_names]], dtype=np.float32)
    return vector, risk_label


def process_training_frame(patient_df: pd.DataFrame) -> ProcessedData:
    processed_df = patient_df.copy()

    expected_numeric = [
        "age",
        "gender",
        "num_prior_admissions",
        "num_chronic_conditions",
        "num_medications",
        "readmitted_30d",
    ]
    for col in expected_numeric:
        processed_df[col] = pd.to_numeric(processed_df[col], errors="coerce")

    processed_df["primary_diagnosis_category"] = processed_df["primary_diagnosis_category"].astype(str)

    for col in expected_numeric:
        processed_df[col] = processed_df[col].fillna(processed_df[col].median())

    processed_df["primary_diagnosis_category"] = processed_df["primary_diagnosis_category"].fillna(
        processed_df["primary_diagnosis_category"].mode()[0]
    )

    processed_df["gender"] = processed_df["gender"].astype(int)

    diag_dummies = pd.get_dummies(
        processed_df["primary_diagnosis_category"],
        prefix="diag",
        drop_first=False,
        dtype=int,
    )
    for category in DIAGNOSIS_CATEGORIES:
        column_name = f"diag_{category}"
        if column_name not in diag_dummies:
            diag_dummies[column_name] = 0
    diag_dummies = diag_dummies[[f"diag_{category}" for category in DIAGNOSIS_CATEGORIES]]

    processed_df = pd.concat(
        [processed_df.drop(columns=["primary_diagnosis_category"]), diag_dummies],
        axis=1,
    )

    processed_df["comorbidity_score"] = (
        processed_df["num_chronic_conditions"] * 1.5
        + processed_df["num_prior_admissions"] * 1.2
        + processed_df["num_medications"] * 0.5
    ).clip(upper=30)

    processed_df["risk_tier_label"] = pd.cut(
        processed_df["comorbidity_score"],
        bins=TIER_BINS,
        labels=TIER_LABELS,
        include_lowest=True,
    )
    processed_df["risk_tier"] = processed_df["risk_tier_label"].map(TIER_MAP).astype(int)

    processed_df["age_group_label"] = pd.cut(
        processed_df["age"],
        bins=AGE_BINS,
        labels=AGE_LABELS,
        include_lowest=True,
    )
    processed_df["age_group"] = processed_df["age_group_label"].map(AGE_MAP).astype(int)

    processed_df["admissions_x_conditions"] = (
        processed_df["num_prior_admissions"] * processed_df["num_chronic_conditions"]
    )

    processed_df = processed_df.drop(columns=["risk_tier_label", "age_group_label"])

    y = processed_df["readmitted_30d"].to_numpy(dtype=int)
    feature_names = [col for col in processed_df.columns if col != "readmitted_30d"]
    X = processed_df[feature_names].to_numpy(dtype=float)

    if not np.isfinite(X).all():
        raise ValueError("Feature matrix contains non-finite values")
    if processed_df.isnull().sum().sum() != 0:
        raise ValueError("Processed frame still contains nulls")

    return ProcessedData(frame=processed_df, X=X, y=y, feature_names=feature_names)
