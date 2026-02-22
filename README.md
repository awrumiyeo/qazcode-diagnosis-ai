# Medical Diagnosis Assistant  
**Symptoms → ICD-10 (Kazakhstan Clinical Protocols)**

Datasaur 2026 | Qazcode Challenge

---

## Overview

This repository contains an MVP **medical diagnosis assistant** that converts
**free-text patient symptoms** into **ranked diagnoses with ICD-10 codes**,
based on **official clinical protocols of the Republic of Kazakhstan**.

The system is fully self-contained:
- runs **offline during inference**
- uses **GPT-OSS (local endpoint only)**
- makes **no external API or network calls**

---

## What the system does

Given a symptom description, the system returns:
- Top-N probable diagnoses
- ICD-10 code for each diagnosis
- Short explanation based on clinical protocols
- Follow-up clinical questions

---

## High-level pipeline

Symptoms (text)  
→ Semantic retrieval over clinical protocols  
→ Candidate ranking  
→ ICD code normalization  
→ Follow-up question generation (GPT-OSS)  
→ JSON response

---

## Technologies used

- **FastAPI** — backend API
- **Sentence-Transformers** — semantic embeddings
- **FAISS** — vector search index
- **Rule-based ranking** — ICD normalization and scoring
- **GPT-OSS** — follow-up question generation (local)
- **Docker** — containerized deployment
- **Streamlit** — simple demo UI

Embedding model:
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
---

## Data Source

Official **Kazakhstan clinical protocols** issued by the Ministry of Health.

Each protocol is stored as JSON with fields:
- `protocol_id`
- `text`
- `icd_codes`

---

## Project Structure
qazcode-diagnosis-ai/
├── data/
│   ├── raw/protocols/        # Clinical protocol corpus
│   ├── index/                # FAISS index + metadata
│   ├── test_set/             # Public evaluation dataset
│   └── evals/                # Evaluation results
├── src/
│   ├── api/
│   │   └── main.py           # FastAPI entrypoint
│   ├── engine/
│   │   ├── retrieve.py       # Vector retrieval
│   │   ├── rank.py           # Ranking & ICD normalization
│   │   ├── icd.py            # ICD helpers
│   │   └── indexing.py       # Index utilities
│   └── llm/
│       └── gpt_oss.py        # GPT-OSS integration
├── app.py                    # Streamlit demo UI
├── build_index.py            # Builds FAISS index
├── evaluate.py               # Official evaluation script
├── Dockerfile
├── requirements.txt
└── README.md

---

## Running locally

### 1. Clone repository

```bash
git clone <your-repository-url>
cd qazcode-diagnosis-ai
```

### 2. Create environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run FastAPI backend
```bash
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```
API will be available at:
```bash
	•	http://127.0.0.1:8000
	•	Swagger UI: http://127.0.0.1:8000/docs
```
### 4. Run Streamlit UI

In a separate terminal:
```bash
streamlit run src/ui/app.py
```

UI will be available at:
```bash
	•	http://localhost:8501
```

### Example API request
```bash
curl -X POST http://127.0.0.1:8000/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": "Острая боль в спине после падения, усиливается при движении"
  }'
```

### Evaluation

Evaluation follows the official Qazcode pipeline.

Metrics:
	•	Accuracy@1
	•	Recall@3
	•	Latency

Run evaluation on a subset (e.g. 30 samples):
```bash
python evaluate.py \
  --name quick_test \
  --endpoint http://127.0.0.1:8000/diagnose \
  --dataset-dir data/test_set \
  --parallelism 2
```

Results are saved to: data/evals/


### Docker

Build image:
```bash
docker build -t qazcode-diagnosis-ai .
```

Run container:
```bash
docker run -p 8080:8080 qazcode-diagnosis-ai
```

Backend will be available at:
```bash
	•	http://localhost:8080
```

(Streamlit UI is intended for local demo, not required for evaluation)
