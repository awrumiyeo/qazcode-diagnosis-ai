import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict


@dataclass
class Chunk:
    protocol_id: str
    icd10_code: str
    diagnosis: str
    text: str
    source_file: str


def load_chunks(protocols_path: Path) -> List[Chunk]:
    """
    1 protocol line may contain multiple icd_codes.
    We create 1 chunk per icd10_code (IMPORTANT for eval alignment).
    """
    chunks: List[Chunk] = []
    with protocols_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            p = json.loads(line)

            protocol_id = p.get("protocol_id", "")
            source_file = p.get("source_file", "")
            title = p.get("title", "") or source_file
            text = p.get("text", "") or ""
            icd_codes = p.get("icd_codes") or []

            # fallback: if empty, still keep one chunk
            if not icd_codes:
                chunks.append(
                    Chunk(
                        protocol_id=protocol_id,
                        icd10_code="",
                        diagnosis=title,
                        text=text,
                        source_file=source_file,
                    )
                )
                continue

            for code in icd_codes:
                chunks.append(
                    Chunk(
                        protocol_id=protocol_id,
                        icd10_code=str(code),
                        diagnosis=title,
                        text=text,
                        source_file=source_file,
                    )
                )

    return chunks


def save_metadata(chunks: List[Chunk], out_path: Path) -> None:
    meta = [
        {
            "protocol_id": c.protocol_id,
            "icd10_code": c.icd10_code,
            "diagnosis": c.diagnosis,
            "source_file": c.source_file,
            "text_preview": c.text[:300],
        }
        for c in chunks
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")