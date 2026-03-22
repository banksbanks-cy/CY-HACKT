import re
from html import unescape


def clean_html(raw_text: str | None) -> str:
    if not raw_text:
        return ""

    text = re.sub(r"<[^>]+>", " ", raw_text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    return text
