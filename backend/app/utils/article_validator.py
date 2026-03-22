def is_valid_article(article: dict) -> bool:
    """
    Vérifie si un article est exploitable.
    """

    title = (article.get("title") or "").strip()
    content = (article.get("content") or "").strip()
    summary = (article.get("summary") or "").strip()

    # titre obligatoire
    if not title or len(title) < 10:
        return False

    # contenu minimum
    if len(content) < 50 and len(summary) < 50:
        return False

    # éviter les trucs vides / spam
    if title.lower() in ["", "null", "none"]:
        return False

    return True
