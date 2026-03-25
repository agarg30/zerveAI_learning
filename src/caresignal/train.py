from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from caresignal.data import generate_synthetic_patients
from caresignal.features import ProcessedData, process_training_frame


ARTIFACT_DIR = Path("artifacts")
MODEL_PATH = ARTIFACT_DIR / "model.joblib"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"
RISK_TABLE_PATH = ARTIFACT_DIR / "risk_table.csv"
CLINICAL_SUMMARIES_PATH = ARTIFACT_DIR / "clinical_summaries.csv"


@dataclass
class TrainingArtifacts:
    model: GradientBoostingClassifier
    processed: ProcessedData
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    y_pred_proba: np.ndarray
    risk_table: pd.DataFrame
    metrics: dict


def build_risk_table(
    processed: ProcessedData,
    test_indices: np.ndarray,
    y_pred_proba: np.ndarray,
    shap_values: np.ndarray,
) -> pd.DataFrame:
    tier_name_map = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
    test_rows = processed.frame.iloc[test_indices].reset_index(drop=True)
    abs_shap = np.abs(shap_values)
    top3_idx = np.argsort(abs_shap, axis=1)[:, -3:][:, ::-1]

    risk_table = pd.DataFrame(
        {
            "patient_id": test_indices + 1,
            "age": test_rows["age"].values,
            "gender": test_rows["gender"].map({0: "F", 1: "M"}).values,
            "risk_score": np.round(y_pred_proba, 4),
            "risk_tier": test_rows["risk_tier"].map(tier_name_map).values,
            "top_driver_1": [processed.feature_names[top3_idx[i, 0]] for i in range(len(test_indices))],
            "top_driver_2": [processed.feature_names[top3_idx[i, 1]] for i in range(len(test_indices))],
            "top_driver_3": [processed.feature_names[top3_idx[i, 2]] for i in range(len(test_indices))],
        }
    )
    return risk_table.sort_values("risk_score", ascending=False).reset_index(drop=True)


def train_model(seed: int = 42) -> TrainingArtifacts:
    patient_df = generate_synthetic_patients(seed=seed)
    processed = process_training_frame(patient_df)

    all_indices = np.arange(len(processed.frame))
    train_idx, test_idx = train_test_split(
        all_indices,
        test_size=0.20,
        random_state=seed,
        stratify=processed.y,
    )

    X_train = processed.X[train_idx]
    X_test = processed.X[test_idx]
    y_train = processed.y[train_idx]
    y_test = processed.y[test_idx]

    model = GradientBoostingClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        validation_fraction=0.1,
        n_iter_no_change=30,
        tol=1e-4,
        random_state=seed,
    )
    model.fit(X_train, y_train)

    y_pred_proba = model.predict_proba(X_test)[:, 1]

    try:
        import shap

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
    except Exception:
        shap_values = np.zeros_like(X_test)

    risk_table = build_risk_table(processed, test_idx, y_pred_proba, shap_values)

    metrics = {
        "auc_roc": float(roc_auc_score(y_test, y_pred_proba)),
        "brier_score": float(brier_score_loss(y_test, y_pred_proba)),
        "train_size": int(len(train_idx)),
        "test_size": int(len(test_idx)),
        "positive_rate_train": float(y_train.mean()),
        "positive_rate_test": float(y_test.mean()),
        "feature_names": processed.feature_names,
    }

    return TrainingArtifacts(
        model=model,
        processed=processed,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        y_pred_proba=y_pred_proba,
        risk_table=risk_table,
        metrics=metrics,
    )


def save_artifacts(artifacts: TrainingArtifacts) -> None:
    import json

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": artifacts.model,
        "feature_names": artifacts.processed.feature_names,
        "metrics": artifacts.metrics,
    }
    joblib.dump(payload, MODEL_PATH)
    with METRICS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(artifacts.metrics, handle, indent=2)
    artifacts.risk_table.to_csv(RISK_TABLE_PATH, index=False)


def main() -> None:
    artifacts = train_model()
    save_artifacts(artifacts)
    print("Saved model artifact to", MODEL_PATH)
    print("AUC-ROC:", f"{artifacts.metrics['auc_roc']:.4f}")
    print("Brier Score:", f"{artifacts.metrics['brier_score']:.4f}")
    print("Top 5 highest-risk patients:")
    print(artifacts.risk_table.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
