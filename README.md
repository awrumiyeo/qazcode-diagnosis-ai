# Medical Diagnosis Assistant  
Symptoms → ICD-10 (Kazakhstan Clinical Protocols)

Datasaur 2026 | Qazcode Challenge

## Overview

This project is a clinical decision support MVP that converts **free-text patient symptoms**
into **ranked medical diagnoses with ICD-10 codes**, based on **official clinical protocols
of the Republic of Kazakhstan**.

The system is fully self-contained and runs offline during inference.
No external LLM APIs are used.  
LLM functionality is implemented via **GPT-OSS** through a local endpoint.

The project includes:
- FastAPI backend (API for diagnosis)
- Streamlit web interface (simple UI for demo)
- Evaluation script provided by organizers

---

## What the system does

Given a free-text description of symptoms, the system returns:
- Top-N diagnoses
- ICD-10 codes
- Short clinical explanation (from protocol text)
- Ranked results

---

## Architecture (simplified)

Symptoms (text)  
→ Semantic retrieval over clinical protocols  
→ Diagnosis ranking  
→ Confidence normalization  
→ JSON response  

Streamlit UI sends requests to FastAPI.

---

## Technologies

- **FastAPI** — backend API
- **Streamlit** — demo web interface
- **Sentence-Transformers** — semantic embeddings
- **Cosine similarity** — protocol retrieval
- **GPT-OSS** — local LLM (no external calls)
- **Docker** — containerized deployment

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
│   ├── test_set/             # Public evaluation dataset
│   └── evals/                # Evaluation outputs
├── src/
│   ├── api/                  # FastAPI backend
│   ├── engine/               # Retrieval and ranking logic
│   ├── llm/                  # GPT-OSS integration
│   └── ui/                   # Streamlit app
├── evaluate.py               # Evaluation script
├── Dockerfile
├── requirements.txt
└── README.md

---

## Running locally

### 1. Clone repository

```bash
git clone <your-repository-url>
cd qazcode-diagnosis-ai

### 2. Create environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

### 3. Run FastAPI backend
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000

API will be available at:
	•	http://127.0.0.1:8000
	•	Swagger UI: http://127.0.0.1:8000/docs

### 4. Run Streamlit UI

In a separate terminal:
streamlit run src/ui/app.py

UI will be available at:
	•	http://localhost:8501

### Example API request
curl -X POST http://127.0.0.1:8000/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": "Острая боль в спине после падения, усиливается при движении"
  }'


### Evaluation

Evaluation follows the official Qazcode pipeline.

Metrics:
	•	Accuracy@1
	•	Recall@3
	•	Latency

Run evaluation on a subset (e.g. 30 samples):
python evaluate.py \
  --name quick_test \
  --endpoint http://127.0.0.1:8000/diagnose \
  --dataset-dir data/test_set \
  --parallelism 2

Results are saved to: data/evals/


### Docker

Build image: docker build -t qazcode-diagnosis-ai .

Run container: docker run -p 8080:8080 qazcode-diagnosis-ai

Backend will be available at:
	•	http://localhost:8080

(Streamlit UI is intended for local demo, not required for evaluation)