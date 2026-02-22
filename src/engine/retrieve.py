import json
import re
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


DATA_DIR = Path("data/test_set")
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

model = SentenceTransformer(MODEL_NAME)

CHUNK_SIZE = 400
CHUNK_OVERLAP = 100

_CORPUS = []
_EMBEDDINGS = None


def chunk_text(text: str) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i : i + CHUNK_SIZE]
        chunks.append(" ".join(chunk))
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def extract_keywords(text: str) -> set:
    tokens = re.findall(r"[а-яa-z]{4,}", text.lower())
    return set(tokens)


def load_corpus():
    global _CORPUS, _EMBEDDINGS
    if _CORPUS:
        return

    texts = []
    meta = []

    for file in DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        gt = data["gt"]
        protocol_text = data["text"]

        chunks = chunk_text(protocol_text)
        for chunk in chunks:
            texts.append(chunk)
            meta.append(
                {
                    "icd10_code": gt,
                    "text": chunk,
                    "keywords": extract_keywords(chunk),
                }
            )

    _EMBEDDINGS = model.encode(texts, normalize_embeddings=True)
    _CORPUS.extend(meta)


def keyword_boost(query: str, chunk_keywords: set) -> float:
    q_keywords = extract_keywords(query)
    overlap = q_keywords & chunk_keywords
    return 0.1 * len(overlap)


def retrieve(query: str, top_k: int = 3) -> List[Dict]:
    load_corpus()

    q_emb = model.encode([query], normalize_embeddings=True)
    sims = cosine_similarity(q_emb, _EMBEDDINGS)[0]

    scores = []
    for i, sim in enumerate(sims):
        boost = keyword_boost(query, _CORPUS[i]["keywords"])
        scores.append(sim + boost)

    top_idx = np.argsort(scores)[::-1][:20]

    agg = defaultdict(list)
    for i in top_idx:
        icd = _CORPUS[i]["icd10_code"]
        agg[icd].append(scores[i])

    ranked = sorted(
        agg.items(), key=lambda x: np.mean(x[1]), reverse=True
    )[:top_k]

    results = []
    for rank, (icd, score_list) in enumerate(ranked, start=1):
        results.append(
            {
                "rank": rank,
                "diagnosis": icd,
                "icd10_code": icd,
                "explanation": f"Matched via {len(score_list)} relevant protocol fragments",
            }
        )

    return results