from fastapi import FastAPI
from pydantic import BaseModel

from src.engine.retrieve import retrieve

app = FastAPI(title="Medical Diagnosis Assistant")


class QueryRequest(BaseModel):
    symptoms: str


@app.post("/diagnose")
def diagnose(req: QueryRequest):
    diagnoses = retrieve(req.symptoms, top_k=3)
    return {"diagnoses": diagnoses}