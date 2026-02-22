import os
import requests
from typing import List

GPT_OSS_URL = os.getenv("GPT_OSS_URL", "").strip()
GPT_OSS_TIMEOUT = float(os.getenv("GPT_OSS_TIMEOUT", "25"))


def _ensure_configured():
    if not GPT_OSS_URL:
        raise RuntimeError(
            "GPT_OSS_URL is not set. Set env GPT_OSS_URL to the local GPT-OSS endpoint."
        )


def generate_followup_questions(symptoms: str, n: int = 3) -> List[str]:
    """
    Использует Kazcode GPT-OSS 120B через ЛОКАЛЬНЫЙ endpoint (без внешних вызовов).
    Возвращает короткие уточняющие клинические вопросы НА РУССКОМ ЯЗЫКЕ.
    """
    _ensure_configured()

    prompt = (
        "Ты — клинический ассистент.\n"
        "На основе описания симптомов задай "
        f"{n} коротких уточняющих вопросов.\n"
        "НЕ ставь диагноз.\n"
        "Верни ТОЛЬКО JSON-массив строк на русском языке.\n\n"
        f"Симптомы: {symptoms}"
    )

    payload = {
        "prompt": prompt,
        "max_tokens": 200,
        "temperature": 0.2,
    }

    r = requests.post(GPT_OSS_URL, json=payload, timeout=GPT_OSS_TIMEOUT)
    r.raise_for_status()

    data = r.json()

    text = None
    if isinstance(data, dict) and "text" in data:
        text = data["text"]
    elif isinstance(data, dict) and "choices" in data and data["choices"]:
        text = data["choices"][0].get("text")

    if not text:
        return [
            "Когда начались симптомы?",
            "Есть ли повышение температуры или давления?",
            "Есть ли ухудшение состояния со временем?",
        ][:n]

    try:
        import json
        arr = json.loads(text)
        if isinstance(arr, list):
            arr = [str(x).strip() for x in arr if str(x).strip()]
            return arr[:n] if arr else []
    except Exception:
        pass

    return [
        "Когда начались симптомы?",
        "Есть ли повышение температуры или давления?",
        "Есть ли ухудшение состояния со временем?",
    ][:n]
