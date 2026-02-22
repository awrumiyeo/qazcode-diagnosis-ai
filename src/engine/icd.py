# src/engine/icd.py

def normalize_icd(code: str) -> str:
    """
    Normalize ICD-10 code for hierarchical matching.
    Examples:
      I63.9 -> I63
      S22.0 -> S22
    """
    if not code:
        return ""
    return code.split(".")[0]