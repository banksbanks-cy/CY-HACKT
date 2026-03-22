import re


CVE_PATTERN = re.compile(r"\bCVE[-\s](\d{4})-(\d{4,7})\b", re.IGNORECASE)


def extract_cves(text: str) -> list[str]:
    if not text:
        return []

    matches = CVE_PATTERN.findall(text)
    normalized = {f"CVE-{year}-{num}" for year, num in matches}

    return sorted(normalized)
