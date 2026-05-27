from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import pandas as pd
import joblib

app = FastAPI(
    title="NurseAssist Triage API",
    description="ML API for predicting patient appointment triage priority",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load("nurseassist_triage_model.joblib")
feature_info = joblib.load("nurseassist_feature_info.joblib")

FEATURES = feature_info["features"]


class PatientInput(BaseModel):
    sex: int = Field(..., ge=1, description="Encoded patient sex, e.g. 1 or 2")

    age: int = Field(..., ge=0, le=120)

    patients_number_per_hour: int = Field(..., ge=0, le=100)

    arrival_mode: int = Field(..., ge=1, description="Encoded arrival mode")

    injury: int = Field(..., ge=0, description="Encoded injury status")

    chief_complain: str = Field(..., min_length=2)

    mental: int = Field(..., ge=1, description="Encoded mental status")

    pain: int = Field(..., ge=0, description="Encoded pain status")

    nrs_pain: int = Field(..., ge=0, le=10)

    sbp: int = Field(..., ge=40, le=250)

    dbp: int = Field(..., ge=20, le=160)

    hr: int = Field(..., ge=20, le=250)

    rr: int = Field(..., ge=5, le=80)

    bt: float = Field(..., ge=30.0, le=45.0)

    saturation: Optional[float] = Field(None, ge=50.0, le=100.0)


def patient_input_to_dataframe(patient: PatientInput) -> pd.DataFrame:
    """
    Convert validated API input into a dataframe with the exact
    column names expected by the trained ML pipeline.
    """

    row = {
        "Sex": patient.sex,
        "Age": patient.age,
        "Patients number per hour": patient.patients_number_per_hour,
        "Arrival mode": patient.arrival_mode,
        "Injury": patient.injury,
        "Chief_complain": patient.chief_complain,
        "Mental": patient.mental,
        "Pain": patient.pain,
        "NRS_pain": patient.nrs_pain,
        "SBP": patient.sbp,
        "DBP": patient.dbp,
        "HR": patient.hr,
        "RR": patient.rr,
        "BT": patient.bt,
        "Saturation": patient.saturation,
    }

    input_df = pd.DataFrame([row])

    # Ensure column order exactly matches training
    input_df = input_df[FEATURES]

    return input_df


@app.get("/")
def root():
    return {
        "message": "NurseAssist Triage API is running",
        "expected_features": FEATURES,
    }


@app.post("/predict")
def predict_priority(patient: PatientInput):
    input_df = patient_input_to_dataframe(patient)

    prediction = model.predict(input_df)[0]

    response = {"predicted_priority": prediction}

    if hasattr(model.named_steps["model"], "predict_proba"):
        probabilities = model.predict_proba(input_df)[0]
        classes = model.named_steps["model"].classes_

        response["probabilities"] = {
            class_name: float(probability)
            for class_name, probability in zip(classes, probabilities)
        }

    return response
