import re
import hashlib


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def generate_signature(title: str, summary: str, content: str) -> str:
    base = f"{title} {summary} {content}"
    normalized = normalize_text(base)

    # on limite pour éviter bruit
    short = normalized[:500]

    return hashlib.md5(short.encode()).hexdigest()
