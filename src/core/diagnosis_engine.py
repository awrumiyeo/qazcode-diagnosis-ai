from typing import List, Dict
import math


SYMPTOM_HINTS = {
    "кашель": {"J13", "J14", "J15", "J18"},
    "мокрот": {"J13", "J18"},
    "одышк": {"J13", "J18", "I50"},
    "боль в груди": {"J13", "I21"},
    "правой нижн": {"K35"},
    "перекос лица": {"I63", "I61"},
    "нарушение речи": {"I63"},
}

BAD_CONTEXT = {
    "неврология": ["тиреоидит"],
    "острый живот": ["астма", "анафилак"],
}


def detect_context(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["перекос", "речь", "слабость"]):
        return "неврология"
    if any(w in q for w in ["живот", "тошнота", "рвота"]):
        return "острый живот"
    return "general"


def emergency_override(query: str) -> List[Dict] | None:
    q = query.lower()
    if ("перекос" in q or "нарушение речи" in q) and "внезап" in q:
        return [
            {
                "name": "Ишемический инсульт",
                "icd10_code": "I63",
                "protocol_id": "emergency_stroke",
                "score": 1.0,
                "evidence": ["Экстренное правило: подозрение на инсульт"],
            },
            {
                "name": "Транзиторная ишемическая атака",
                "icd10_code": "G45",
                "protocol_id": "fallback_tia",
                "score": 0.7,
                "evidence": ["Дифференциальная диагностика"],
            },
            {
                "name": "Гипертонический криз",
                "icd10_code": "I16",
                "protocol_id": "fallback_htn",
                "score": 0.6,
                "evidence": ["Возможный триггер симптомов"],
            },
        ]
    return None


def apply_boosting(query: str, c: Dict) -> float:
    boost = 0.0
    q = query.lower()
    for kw, codes in SYMPTOM_HINTS.items():
        if kw in q and c["icd10_code"] in codes:
            boost += 0.15
    return boost


def is_blacklisted(context: str, name: str) -> bool:
    name = name.lower()
    for bad in BAD_CONTEXT.get(context, []):
        if bad in name:
            return True
    return False


def normalize_confidence(cands: List[Dict]) -> None:
    max_score = max(c["score"] for c in cands) or 1.0
    for c in cands:
        c["confidence"] = round(c["score"] / max_score, 2)



def build_diagnoses(
    query: str,
    retrieved: List[Dict],
    top_k: int = 3,
) -> List[Dict]:

    # 1. Emergency
    emergency = emergency_override(query)
    if emergency:
        normalize_confidence(emergency)
        return emergency[:top_k]

    context = detect_context(query)
    candidates = []

    # 2. Retrieval + rules
    for r in retrieved:
        if "diagnosis" not in r or "icd10_code" not in r:
            continue

        if is_blacklisted(context, r["diagnosis"]):
            continue

        score = r.get("score", 0.5)
        score += apply_boosting(query, r)

        candidates.append({
            "name": r["diagnosis"],
            "icd10_code": r["icd10_code"],
            "protocol_id": r.get("protocol_id", "unknown"),
            "score": score,
            "evidence": r.get("evidence", []),
        })

    # 3. Sort
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # 4. Fallback if < K
    if len(candidates) < top_k:
        candidates.extend(contextual_fallback(query, candidates))

    # 5. Cut + normalize
    candidates = candidates[:top_k]
    normalize_confidence(candidates)
    return candidates


def contextual_fallback(query: str, used: List[Dict]) -> List[Dict]:
    q = query.lower()
    used_codes = {c["icd10_code"] for c in used}
    pool = []

    if any(w in q for w in ["кашель", "температур", "мокрот"]):
        pool = [
            ("Внебольничная пневмония", "J18"),
            ("Острый бронхит", "J20"),
            ("ОРВИ", "J06"),
        ]
    elif any(w in q for w in ["живот", "правой нижн"]):
        pool = [
            ("Острый аппендицит", "K35"),
            ("Гастроэнтерит", "A09"),
            ("Кишечная колика", "K59"),
        ]
    elif any(w in q for w in ["беремен", "давление"]):
        pool = [
            ("Преэклампсия", "O14"),
            ("HELLP-синдром", "O14"),
            ("Гипертензия при беременности", "O10"),
        ]
    else:
        pool = [
            ("Артериальная гипертензия", "I10"),
            ("Астенический синдром", "R53"),
            ("Вегетативная дисфункция", "G90"),
        ]

    out = []
    for name, code in pool:
        if code not in used_codes:
            out.append({
                "name": name,
                "icd10_code": code,
                "protocol_id": "context_fallback",
                "score": 0.4,
                "evidence": ["Контекстный fallback"],
            })
    return out