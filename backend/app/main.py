from time import perf_counter

from fastapi import FastAPI, HTTPException, Query

from app.core.logging import setup_logger
from app.db import get_connection
from app.models.article import enrich_article, enrich_articles
from app.services.article_service import (
    delete_old_articles,
    get_all_articles,
    get_article_by_id,
    get_articles_by_category,
    get_articles_by_cve,
    get_critical_articles,
    get_latest_articles,
    get_stats,
    get_top_threats,
    save_articles,
    search_articles,
)
from app.services.cisa_service import fetch_cisa_articles
from app.services.rss_service import fetch_articles

logger = setup_logger("cyhackt.api")

app = FastAPI(title="CY-HACKT API")


def normalize_limit(limit: int, max_limit: int = 100) -> int:
    if limit < 1:
        return 1
    if limit > max_limit:
        return max_limit
    return limit


@app.get("/")
def root():
    return {"message": "CY-HACKT API is running"}


@app.get("/ingest")
def ingest():
    start = perf_counter()
    logger.info("Ingest endpoint called")

    rss_articles = fetch_articles()
    cisa_articles = fetch_cisa_articles()

    all_articles = rss_articles + cisa_articles
    result = save_articles(all_articles)

    duration = round(perf_counter() - start, 3)

    logger.info(
        f"Ingest completed rss={len(rss_articles)} cisa={len(cisa_articles)} "
        f"total={len(all_articles)} inserted={result['inserted']} duration={duration}s"
    )

    return {
        "status": "success",
        "message": "Ingestion completed",
        "duration_seconds": duration,
        "sources": {
            "rss": len(rss_articles),
            "cisa": len(cisa_articles),
            "total": len(all_articles),
        },
        "result": result,
    }


@app.delete("/reset")
def reset_db():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("TRUNCATE TABLE articles;")
        conn.commit()

        logger.warning("Database reset executed")
        return {"status": "database reset"}

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Reset failed error={str(e)}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/cleanup")
def cleanup_old_articles(days: int = 30):
    deleted = delete_old_articles(days)

    return {
        "status": "success",
        "message": "Old articles deleted",
        "deleted": deleted,
        "days": days,
    }


@app.get("/stats")
def stats():
    data = get_stats()

    if "top_threats" in data:
        data["top_threats"] = [enrich_article(article) for article in data["top_threats"]]

    return data


@app.get("/articles")
def list_articles(limit: int = 50, offset: int = 0):
    limit = normalize_limit(limit)
    offset = max(offset, 0)

    articles = get_all_articles(limit=limit, offset=offset)
    articles = enrich_articles(articles)

    return {
        "count": len(articles),
        "limit": limit,
        "offset": offset,
        "articles": articles,
    }


@app.get("/articles/{article_id}")
def read_article(article_id: int):
    article = get_article_by_id(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return enrich_article(article)


@app.get("/articles/category/{category}")
def read_articles_by_category(category: str, limit: int = 20, offset: int = 0):
    limit = normalize_limit(limit)
    offset = max(offset, 0)

    articles = get_articles_by_category(category=category, limit=limit, offset=offset)
    articles = enrich_articles(articles)

    return {
        "count": len(articles),
        "category": category,
        "limit": limit,
        "offset": offset,
        "articles": articles,
    }


@app.get("/articles/cve/{cve_id}")
def read_articles_by_cve(cve_id: str, limit: int = 20, offset: int = 0):
    limit = normalize_limit(limit)
    offset = max(offset, 0)

    articles = get_articles_by_cve(cve_id=cve_id, limit=limit, offset=offset)
    articles = enrich_articles(articles)

    return {
        "count": len(articles),
        "cve": cve_id.upper(),
        "limit": limit,
        "offset": offset,
        "articles": articles,
    }


@app.get("/latest")
def latest_articles(limit: int = 20, offset: int = 0):
    limit = normalize_limit(limit)
    offset = max(offset, 0)

    articles = get_latest_articles(limit=limit, offset=offset)
    articles = enrich_articles(articles)

    return {
        "count": len(articles),
        "limit": limit,
        "offset": offset,
        "articles": articles,
    }


@app.get("/critical")
def critical_articles(limit: int = 20, offset: int = 0, min_score: int = 4):
    limit = normalize_limit(limit)
    offset = max(offset, 0)

    if min_score < 1:
        min_score = 1
    if min_score > 5:
        min_score = 5

    articles = get_critical_articles(limit=limit, offset=offset, min_score=min_score)
    articles = enrich_articles(articles)

    return {
        "count": len(articles),
        "limit": limit,
        "offset": offset,
        "min_score": min_score,
        "articles": articles,
    }


@app.get("/top-threats")
def top_threats(limit: int = 10):
    limit = normalize_limit(limit, max_limit=50)

    articles = get_top_threats(limit=limit)
    articles = enrich_articles(articles)

    return {
        "count": len(articles),
        "limit": limit,
        "articles": articles,
    }


@app.get("/search")
def search(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = 20,
    offset: int = 0,
):
    limit = normalize_limit(limit)
    offset = max(offset, 0)

    articles = search_articles(query_text=q, limit=limit, offset=offset)
    articles = enrich_articles(articles)

    return {
        "count": len(articles),
        "query": q,
        "limit": limit,
        "offset": offset,
        "articles": articles,
    }
