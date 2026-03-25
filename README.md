# zerveAI_learning
🏥 CareSignal /assess API — Documentation

Base URL: https://1a9b29f1-57c1475c.hub.zerve.cloud
Full Endpoint: https://1a9b29f1-57c1475c.hub.zerve.cloud/assess
Version: v1
Model: Gradient Boosting Classifier (AUC-ROC: 0.676 · Brier Score: 0.189)


Overview
The /assess endpoint predicts a patient's 30-day hospital readmission risk using a trained gradient boosting model with SHAP-based explainability. Given six clinical input fields, it returns a risk score, risk tier classification, the top 3 contributing risk drivers, and an AI-generated clinical narrative.

Endpoint Reference
PropertyValueURLhttps://1a9b29f1-57c1475c.hub.zerve.cloud/assessMethodPOSTAuthBearer token (set Authorization: Bearer <token> header)Content-Typeapplication/jsonAcceptapplication/json

Request Body
Send a JSON object with the following fields:
{
  "age": 52,
  "gender": "F",
  "prior_admissions": 2,
  "chronic_conditions": 3,
  "primary_diagnosis": "Diabetes",
  "medications": 6
}

Request Field Schema
FieldTypeRequiredDescriptionExampleageinteger✅ YesPatient age in years. Categorised internally as Young (≤35), Middle (36–55), Senior (56–70), Elderly (71+).52genderstring✅ YesBiological sex. Accepts "M" (male) or "F" (female). Case-insensitive."F"prior_admissionsinteger✅ YesNumber of prior hospital admissions. Non-negative integer.2chronic_conditionsinteger✅ YesNumber of active chronic conditions (e.g., hypertension, COPD). Non-negative integer.3primary_diagnosisstring✅ YesPrimary diagnosis category. Must be one of: Cardiac, Respiratory, Diabetes, Oncology, Neurological, Other. Case-insensitive. Unknown values map to Other."Diabetes"medicationsinteger✅ YesTotal number of current medications prescribed. Non-negative integer.6

Note: All six fields are required. The model will return a 422 Unprocessable Entity error if any field is missing or of the wrong type.


Response Body
A successful 200 OK response returns:
{
  "patient_input": {
    "age": 52,
    "gender": "F",
    "prior_admissions": 2,
    "chronic_conditions": 3,
    "primary_diagnosis": "Diabetes",
    "medications": 6
  },
  "risk_score": 0.2485,
  "risk_tier": "Medium",
  "top_drivers": [
    "age",
    "admissions_x_conditions",
    "diag_Diabetes"
  ],
  "ai_clinical_summary": "This 52-year-old female patient carries a medium 30-day readmission risk (score 0.2485), driven primarily by advanced age and a high admissions-to-conditions interaction score. Additional concern is noted for a primary diabetes diagnosis, warranting close post-discharge monitoring and timely outpatient follow-up."
}

Response Field Schema
FieldTypeDescriptionpatient_inputobjectEcho of the original request fields for traceability.patient_input.ageintegerPatient age as submitted.patient_input.genderstringPatient gender as submitted ("M" or "F").patient_input.prior_admissionsintegerPrior admissions count as submitted.patient_input.chronic_conditionsintegerChronic conditions count as submitted.patient_input.primary_diagnosisstringPrimary diagnosis category as submitted.patient_input.medicationsintegerMedication count as submitted.risk_scorefloatPredicted probability of 30-day readmission. Range: 0.0 – 1.0. Rounded to 4 decimal places.risk_tierstringCategorical risk classification derived from a comorbidity score. One of: Low, Medium, High, Critical.top_driversarray[string]Top 3 feature names ranked by absolute SHAP value (most impactful first). See driver label reference below.ai_clinical_summarystringRule-based two-sentence clinical narrative summarising the risk score, tier, and top drivers in plain English.
Risk Tier Reference
Tiers are computed from an internal comorbidity score = min(chronic_conditions × 1.5 + prior_admissions × 1.2 + medications × 0.5, 30):
TierComorbidity Score RangeTypical Risk Score RangeLow0 – 7.5~0.10 – 0.25Medium7.5 – 15.0~0.20 – 0.40High15.0 – 22.5~0.40 – 0.70Critical22.5 – 30.0~0.65 – 0.95
Top Driver Label Reference
Feature NameHuman Readable Labelcomorbidity_scorea high comorbidity burdenageadvanced agenum_medicationsa high medication countnum_chronic_conditionsmultiple chronic conditionsnum_prior_admissionsfrequent prior hospital admissionsadmissions_x_conditionsa high admissions-to-conditions interaction scoreage_groupage-related risk factorsdiag_Cardiaca primary cardiac diagnosisdiag_Diabetesa primary diabetes diagnosisdiag_Respiratorya primary respiratory diagnosisdiag_Oncologya primary oncology diagnosisdiag_Neurologicala primary neurological diagnosisdiag_Othera complex multi-system diagnosis

Example Requests & Responses
Example 1 — Low Risk Patient
Request:
{
  "age": 28,
  "gender": "F",
  "prior_admissions": 0,
  "chronic_conditions": 1,
  "primary_diagnosis": "Respiratory",
  "medications": 2
}

Response (200 OK):
{
  "patient_input": {
    "age": 28,
    "gender": "F",
    "prior_admissions": 0,
    "chronic_conditions": 1,
    "primary_diagnosis": "Respiratory",
    "medications": 2
  },
  "risk_score": 0.1948,
  "risk_tier": "Low",
  "top_drivers": ["comorbidity_score", "age", "admissions_x_conditions"],
  "ai_clinical_summary": "This 28-year-old female patient carries a low 30-day readmission risk (score 0.1948), driven primarily by a high comorbidity burden and advanced age. Additional concern is noted for a high admissions-to-conditions interaction score, warranting close post-discharge monitoring and timely outpatient follow-up."
}


Example 2 — High Risk Patient
Request:
{
  "age": 82,
  "gender": "M",
  "prior_admissions": 5,
  "chronic_conditions": 6,
  "primary_diagnosis": "Cardiac",
  "medications": 12
}

Response (200 OK):
{
  "patient_input": {
    "age": 82,
    "gender": "M",
    "prior_admissions": 5,
    "chronic_conditions": 6,
    "primary_diagnosis": "Cardiac",
    "medications": 12
  },
  "risk_score": 0.7231,
  "risk_tier": "High",
  "top_drivers": ["comorbidity_score", "num_prior_admissions", "num_medications"],
  "ai_clinical_summary": "This 82-year-old male patient carries a high 30-day readmission risk (score 0.7231), driven primarily by a high comorbidity burden and frequent prior hospital admissions. Additional concern is noted for a high medication count, warranting close post-discharge monitoring and timely outpatient follow-up."
}


Error Codes
HTTP StatusError CodeDescription400Bad RequestMalformed JSON body or invalid field value (e.g., prior_admissions: -1).401UnauthorizedMissing or invalid Authorization bearer token.422Unprocessable EntityOne or more required fields are missing or of the wrong type.429Too Many RequestsRate limit exceeded. Retry after the Retry-After header value (seconds).500Internal Server ErrorUnexpected server-side error. Contact support if the issue persists.
Example 422 Response:
{
  "detail": [
    {
      "loc": ["body", "primary_diagnosis"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}


Code Examples
cURL
curl -X POST "https://1a9b29f1-57c1475c.hub.zerve.cloud/assess" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "age": 65,
    "gender": "M",
    "prior_admissions": 3,
    "chronic_conditions": 4,
    "primary_diagnosis": "Cardiac",
    "medications": 8
  }'


Python (requests)
import requests

url = "https://1a9b29f1-57c1475c.hub.zerve.cloud/assess"

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer <your_token>",
}

payload = {
    "age": 65,
    "gender": "M",
    "prior_admissions": 3,
    "chronic_conditions": 4,
    "primary_diagnosis": "Cardiac",
    "medications": 8,
}

response = requests.post(url, json=payload, headers=headers)
response.raise_for_status()

result = response.json()

print(f"Risk Score : {result['risk_score']}")
print(f"Risk Tier  : {result['risk_tier']}")
print(f"Top Drivers: {', '.join(result['top_drivers'])}")
print(f"Summary    : {result['ai_clinical_summary']}")

Output:
Risk Score : 0.5143
Risk Tier  : High
Top Drivers: comorbidity_score, num_prior_admissions, age
Summary    : This 65-year-old male patient carries a high 30-day readmission risk ...


Python (httpx — async)
import asyncio
import httpx

async def assess_patient_async(patient: dict, token: str) -> dict:
    url = "https://1a9b29f1-57c1475c.hub.zerve.cloud/assess"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=patient, headers=headers)
        response.raise_for_status()
        return response.json()

patient = {
    "age": 52,
    "gender": "F",
    "prior_admissions": 2,
    "chronic_conditions": 3,
    "primary_diagnosis": "Diabetes",
    "medications": 6,
}

result = asyncio.run(assess_patient_async(patient, token="<your_token>"))
print(result)


Notes & Constraints

All 6 request fields are mandatory — omitting any field returns 422.
primary_diagnosis values are case-insensitive. Unrecognised values are silently mapped to "Other".
gender accepts "M" / "m" / "F" / "f" — leading/trailing whitespace is trimmed.
risk_score is a probability (not a percentage) — multiply by 100 to display as %.
The top_drivers list always contains exactly 3 feature names, ranked by SHAP importance.
The ai_clinical_summary is deterministic — the same inputs will always produce the same narrative.
Typical response latency is < 500ms under normal load.
The model was trained on 2,000 synthetic patients with a 30-day readmission base rate of ~29%.
