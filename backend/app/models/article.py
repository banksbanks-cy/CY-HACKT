def get_severity_label(score: int) -> str:
    if score >= 5:
        return "critical"
    if score >= 4:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def get_category_label(category: str) -> str:
    mapping = {
        "zero-day": "Zero-Day",
        "ransomware": "Ransomware",
        "phishing": "Phishing",
        "malware": "Malware",
        "vulnerability": "Vulnerability",
        "data-breach": "Data Breach",
        "patch": "Patch / Update",
        "threat-actor": "Threat Actor",
        "incident": "Incident",
        "other": "Other",
    }
    return mapping.get(category, "Other")


def build_badges(article: dict) -> list[str]:
    badges = []

    score = article.get("score", 1)
    cve_list = article.get("cve_list") or ""
    reason = (article.get("score_reason") or "").lower()
    category = article.get("category", "other")
    source = article.get("source", "")

    if score >= 5:
        badges.append("Critical")
    elif score >= 4:
        badges.append("High")

    if cve_list:
        badges.append("CVE")

    if "rce" in reason or "remote code execution" in reason:
        badges.append("RCE")

    if category == "zero-day":
        badges.append("Zero-Day")

    if category == "ransomware":
        badges.append("Ransomware")

    if source == "CISA":
        badges.append("CISA")

    return badges


def enrich_article(article: dict) -> dict:
    article = dict(article)

    score = article.get("score", 1)
    category = article.get("category", "other")

    article["severity_label"] = get_severity_label(score)
    article["category_label"] = get_category_label(category)
    article["badges"] = build_badges(article)

    return article


def enrich_articles(articles: list[dict]) -> list[dict]:
    return [enrich_article(article) for article in articles]
