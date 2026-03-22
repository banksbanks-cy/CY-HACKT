import re


def split_sentences(text: str) -> list[str]:
    if not text:
        return []

    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [part.strip() for part in parts if part.strip()]


def clean_summary_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_summary(text: str, max_sentences: int = 3, max_chars: int = 400) -> str:
    if not text:
        return ""

    text = clean_summary_text(text)
    sentences = split_sentences(text)

    if sentences:
        summary = " ".join(sentences[:max_sentences]).strip()
    else:
        summary = text[:max_chars].strip()

    if len(summary) > max_chars:
        summary = summary[:max_chars].rsplit(" ", 1)[0].strip() + "..."

    return summary
