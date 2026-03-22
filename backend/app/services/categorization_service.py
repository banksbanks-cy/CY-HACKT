def categorize_article(text: str) -> str:
    if not text:
        return "other"

    text = text.lower()

    category_rules = {
        "zero-day": [
            "zero-day",
            "0-day",
            "actively exploited",
            "exploit in the wild",
            "known exploited vulnerability",
        ],
        "ransomware": [
            "ransomware",
            "double extortion",
            "extortion",
        ],
        "phishing": [
            "phishing",
            "credential theft",
            "email scam",
            "social engineering",
        ],
        "malware": [
            "malware",
            "trojan",
            "spyware",
            "botnet",
            "worm",
            "loader",
            "stealer",
        ],
        "vulnerability": [
            "cve-",
            "vulnerability",
            "rce",
            "remote code execution",
            "authentication bypass",
            "auth bypass",
            "privilege escalation",
            "sql injection",
        ],
        "data-breach": [
            "data breach",
            "breach",
            "leaked data",
            "exposed database",
            "stolen data",
        ],
        "patch": [
            "patch",
            "security update",
            "fix released",
            "patched",
            "updates",
        ],
        "threat-actor": [
            "apt",
            "threat actor",
            "state-sponsored",
            "hacker group",
            "hackers group",
        ],
        "incident": [
            "cyberattack",
            "cyber attack",
            "incident",
            "security incident",
            "compromise",
        ],
    }

    for category, keywords in category_rules.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return "other"
