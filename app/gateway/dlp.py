# app/gateway/dlp.py
import re

PII_PATTERNS = [
    re.compile(r"\b\d{16}\b"),     # ex: carte bancaire (trop simplifié)
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # ex: SSN US (exemple)
]

def dlp_check(text: str) -> tuple[bool, str]:
    for p in PII_PATTERNS:
        if p.search(text):
            return False, "DLP: detected sensitive pattern"
    return True, "OK"
