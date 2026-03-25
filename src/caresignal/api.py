from __future__ import annotations

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from caresignal.inference import assess_patient, load_bundle


app = FastAPI(
    title="CareSignal AI",
    description="30-Day Hospital Readmission Risk Predictor",
    version="0.1.0",
)


class PatientInput(BaseModel):
    age: int = Field(..., ge=18, le=120)
    gender: Literal["M", "F"]
    prior_admissions: int = Field(..., ge=0, le=20)
    chronic_conditions: int = Field(..., ge=0, le=15)
    primary_diagnosis: str
    medications: int = Field(..., ge=0, le=30)


class AssessmentResponse(BaseModel):
    patient_input: dict
    risk_score: float
    risk_tier: str
    top_drivers: list[str]
    ai_clinical_summary: str


@app.get("/")
def root() -> dict:
    return {
        "message": "CareSignal AI — 30-Day Readmission Risk Predictor",
        "endpoints": {
            "POST /assess": "Assess patient readmission risk",
            "GET /health": "Health check and model info",
        },
    }


@app.get("/health")
def health() -> dict:
    bundle = load_bundle()
    return {
        "status": "ok",
        "model": type(bundle["model"]).__name__,
        "auc_roc": bundle["metrics"]["auc_roc"],
        "brier_score": bundle["metrics"]["brier_score"],
    }


@app.post("/assess", response_model=AssessmentResponse)
def assess(payload: PatientInput) -> AssessmentResponse:
    result = assess_patient(**payload.model_dump())
    return AssessmentResponse(**result)
