from app.services.cve_service import extract_cves


def compute_score(text: str) -> int:
    score, _ = compute_score_details(text)
    return score


def compute_score_details(text: str) -> tuple[int, str]:
    if not text:
        return 1, "No meaningful content detected"

    text = text.lower()
    reasons = []
    points = 1.0

    critical_keywords = [
        "zero-day",
        "0-day",
        "rce",
        "remote code execution",
        "actively exploited",
        "exploit in the wild",
        "unauthenticated remote code execution",
        "known exploited vulnerability",
    ]

    high_keywords = [
        "critical vulnerability",
        "authentication bypass",
        "auth bypass",
        "privilege escalation",
        "ransomware",
        "sql injection",
        "command injection",
        "arbitrary code execution",
    ]

    medium_keywords = [
        "phishing",
        "malware",
        "trojan",
        "spyware",
        "botnet",
        "vulnerability",
        "data breach",
        "breach",
        "leak",
        "stealer",
    ]

    found_critical = [kw for kw in critical_keywords if kw in text]
    found_high = [kw for kw in high_keywords if kw in text]
    found_medium = [kw for kw in medium_keywords if kw in text]

    if found_medium:
        points = max(points, 3.0)
        reasons.append(f"Medium indicators: {', '.join(found_medium[:3])}")

    if found_high:
        points = max(points, 4.0)
        reasons.append(f"High-risk indicators: {', '.join(found_high[:3])}")

    if found_critical:
        points = max(points, 5.0)
        reasons.append(f"Critical indicators: {', '.join(found_critical[:3])}")

    cves = extract_cves(text)
    if cves:
        if points < 4.0:
            points = 4.0
        reasons.append(f"CVE detected: {', '.join(cves[:3])}")

        if len(cves) >= 2:
            points += 0.5
            reasons.append("Multiple CVEs detected")

    if "critical" in text and points < 5.0:
        points += 0.5
        reasons.append("Contains critical severity wording")

    final_score = max(1, min(5, round(points)))

    if not reasons:
        reasons.append("Low-risk or generic cyber content")

    return final_score, " | ".join(reasons)
