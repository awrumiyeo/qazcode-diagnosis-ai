from pydantic import BaseModel, Field
from typing import List


class DiagnoseRequest(BaseModel):
    symptoms: str = Field(..., min_length=1)


class DiagnosisItem(BaseModel):
    rank: int
    diagnosis: str
    icd10_code: str
    explanation: str


class DiagnoseResponse(BaseModel):
    diagnoses: List[DiagnosisItem]
    latency_ms: int