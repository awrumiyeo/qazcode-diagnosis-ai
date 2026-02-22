from pathlib import Path
import json

import faiss
from sentence_transformers import SentenceTransformer

from src.engine.indexing import load_chunks, save_metadata

BASE = Path(__file__).resolve().parent
PROTOCOLS = BASE / "data" / "raw" / "protocols" / "protocols_corpus.jsonl"
INDEX_DIR = BASE / "data" / "index"
FAISS_PATH = INDEX_DIR / "embeddings.faiss"
META_PATH = INDEX_DIR / "metadata.json"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main():
    chunks = load_chunks(PROTOCOLS)
    texts = [c.text for c in chunks]

    model = SentenceTransformer(MODEL_NAME)
    embs = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)

    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine if embeddings normalized
    index.add(embs)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_PATH))
    save_metadata(chunks, META_PATH)

    print("OK")
    print("chunks:", len(chunks))
    print("faiss:", FAISS_PATH)
    print("meta:", META_PATH)


if __name__ == "__main__":
    main()