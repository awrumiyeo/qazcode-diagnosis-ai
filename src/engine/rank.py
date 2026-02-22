from typing import List, Dict
import re

def normalize_icd(code: str) -> str:
    """
    Normalize ICD-10 code for evaluation.
    Examples:
      "S22.0 " -> "S22.0"
      "S22.0," -> "S22.0"
      "S22"    -> "S22"
    """
    if not code:
        return ""
    code = code.strip().upper()
    match = re.match(r"^[A-Z]\d{2}(\.\d+)?", code)
    return match.group(0) if match else code

def rank_candidates(items: List[Dict], top_n: int = 3) -> List[Dict]:
    best = {}
    for it in items:
        raw_code = it.get("icd10_code") or ""
        code = normalize_icd(raw_code)
        if not code:
            continue

        it["icd10_code"] = code  # <-- ВАЖНО
        if code not in best or it.get("score", 0) > best[code].get("score", 0):
            best[code] = it

    ranked = sorted(best.values(), key=lambda x: x.get("score", 0), reverse=True)
    return ranked[:top_n]