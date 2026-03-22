from datetime import datetime, timedelta, timezone

from psycopg2.extras import execute_values

from app.core.logging import setup_logger
from app.db import get_connection, get_dict_connection
from app.services.categorization_service import categorize_article
from app.services.cve_service import extract_cves
from app.services.scoring_service import compute_score_details
from app.services.summary_service import generate_summary
from app.utils.deduplicator import generate_signature

logger = setup_logger("cyhackt.article")


def parse_published_at(date_str):
    if not date_str:
        return None

    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def build_full_text(article: dict) -> str:
    return (
        f"{article.get('title', '')} "
        f"{article.get('summary', '')} "
        f"{article.get('content', '')}"
    ).strip()


def normalize_article(article: dict) -> dict:
    return {
        "title": (article.get("title") or "").strip(),
        "link": (article.get("link") or "").strip(),
        "source": (article.get("source") or "").strip(),
        "published_at": article.get("published_at"),
        "summary": (article.get("summary") or "").strip(),
        "content": (article.get("content") or "").strip(),
    }


def prepare_article_row(article: dict):
    full_text = build_full_text(article)

    score, score_reason = compute_score_details(full_text)
    category = categorize_article(full_text)
    cve_list = extract_cves(full_text)
    ai_summary = generate_summary(full_text)
    published_at = parse_published_at(article.get("published_at"))

    return (
        article.get("title"),
        article.get("link"),
        article.get("source"),
        published_at,
        article.get("summary"),
        article.get("content"),
        ai_summary,
        score,
        score_reason,
        category,
        ", ".join(cve_list) if cve_list else None,
    )


def save_articles(articles: list[dict]) -> dict:
    logger.info(f"DB batch save started total_articles={len(articles)}")

    if not articles:
        return {
            "inserted": 0,
            "skipped_duplicates": 0,
            "total_processed": 0,
        }

    seen_signatures = set()
    rows_to_insert = []
    skipped_count = 0

    for raw_article in articles:
        try:
            article = normalize_article(raw_article)

            signature = generate_signature(
                article.get("title"),
                article.get("summary"),
                article.get("content"),
            )

            if signature in seen_signatures:
                skipped_count += 1
                continue

            seen_signatures.add(signature)
            row = prepare_article_row(article)
            rows_to_insert.append(row)

        except Exception as e:
            skipped_count += 1
            logger.exception(
                f"Failed to prepare article title={raw_article.get('title', '')[:80]} error={str(e)}"
            )

    if not rows_to_insert:
        result = {
            "inserted": 0,
            "skipped_duplicates": skipped_count,
            "total_processed": len(articles),
        }
        logger.info(
            f"DB batch save finished inserted=0 skipped={skipped_count} total={len(articles)}"
        )
        return result

    conn = None
    cursor = None

    query = """
        INSERT INTO articles (
            title,
            link,
            source,
            published_at,
            summary,
            content,
            ai_summary,
            score,
            score_reason,
            category,
            cve_list
        )
        VALUES %s
        ON CONFLICT (link) DO NOTHING
    """

    try:
        conn = get_connection()
        cursor = conn.cursor()

        execute_values(
            cursor,
            query,
            rows_to_insert,
            page_size=100,
        )

        inserted_count = cursor.rowcount if cursor.rowcount != -1 else 0
        conn.commit()

        db_conflict_skipped = max(0, len(rows_to_insert) - inserted_count)
        skipped_count += db_conflict_skipped

        result = {
            "inserted": inserted_count,
            "skipped_duplicates": skipped_count,
            "total_processed": len(articles),
        }

        logger.info(
            f"DB batch save finished inserted={inserted_count} "
            f"skipped={skipped_count} prepared={len(rows_to_insert)} total={len(articles)}"
        )

        return result

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"DB batch save failed error={str(e)}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_all_articles(limit: int = 50, offset: int = 0):
    conn = get_dict_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            id,
            title,
            link,
            source,
            published_at,
            summary,
            content,
            ai_summary,
            score,
            score_reason,
            cve_list,
            category,
            created_at
        FROM articles
        ORDER BY published_at DESC NULLS LAST, created_at DESC
        LIMIT %s OFFSET %s
    """

    try:
        cursor.execute(query, (limit, offset))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_latest_articles(limit: int = 20, offset: int = 0):
    conn = get_dict_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            id,
            title,
            link,
            source,
            published_at,
            summary,
            content,
            ai_summary,
            score,
            score_reason,
            cve_list,
            category,
            created_at
        FROM articles
        ORDER BY published_at DESC NULLS LAST, created_at DESC
        LIMIT %s OFFSET %s
    """

    try:
        cursor.execute(query, (limit, offset))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_critical_articles(limit: int = 20, offset: int = 0, min_score: int = 4):
    conn = get_dict_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            id,
            title,
            link,
            source,
            published_at,
            summary,
            content,
            ai_summary,
            score,
            score_reason,
            cve_list,
            category,
            created_at
        FROM articles
        WHERE score >= %s
        ORDER BY score DESC, published_at DESC NULLS LAST, created_at DESC
        LIMIT %s OFFSET %s
    """

    try:
        cursor.execute(query, (min_score, limit, offset))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_top_threats(limit: int = 10):
    conn = get_dict_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            id,
            title,
            link,
            source,
            published_at,
            summary,
            content,
            ai_summary,
            score,
            score_reason,
            cve_list,
            category,
            created_at
        FROM articles
        WHERE score >= 4
        ORDER BY score DESC, published_at DESC NULLS LAST, created_at DESC
        LIMIT %s
    """

    try:
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def search_articles(query_text: str, limit: int = 20, offset: int = 0):
    conn = get_dict_connection()
    cursor = conn.cursor()

    search_term = f"%{query_text.strip()}%"

    query = """
        SELECT
            id,
            title,
            link,
            source,
            published_at,
            summary,
            content,
            ai_summary,
            score,
            score_reason,
            cve_list,
            category,
            created_at
        FROM articles
        WHERE
            title ILIKE %s
            OR summary ILIKE %s
            OR content ILIKE %s
            OR cve_list ILIKE %s
            OR category ILIKE %s
            OR source ILIKE %s
        ORDER BY score DESC, published_at DESC NULLS LAST, created_at DESC
        LIMIT %s OFFSET %s
    """

    try:
        cursor.execute(
            query,
            (
                search_term,
                search_term,
                search_term,
                search_term,
                search_term,
                search_term,
                limit,
                offset,
            ),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_article_by_id(article_id: int):
    conn = get_dict_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            id,
            title,
            link,
            source,
            published_at,
            summary,
            content,
            ai_summary,
            score,
            score_reason,
            cve_list,
            category,
            created_at
        FROM articles
        WHERE id = %s
    """

    try:
        cursor.execute(query, (article_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_articles_by_category(category: str, limit: int = 20, offset: int = 0):
    conn = get_dict_connection()
    cursor = conn.cursor()

    normalized_category = category.strip().lower()

    query = """
        SELECT
            id,
            title,
            link,
            source,
            published_at,
            summary,
            content,
            ai_summary,
            score,
            score_reason,
            cve_list,
            category,
            created_at
        FROM articles
        WHERE category = %s
        ORDER BY score DESC, published_at DESC NULLS LAST, created_at DESC
        LIMIT %s OFFSET %s
    """

    try:
        cursor.execute(query, (normalized_category, limit, offset))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_articles_by_cve(cve_id: str, limit: int = 20, offset: int = 0):
    conn = get_dict_connection()
    cursor = conn.cursor()

    normalized_cve = cve_id.upper()

    query = """
        SELECT
            id,
            title,
            link,
            source,
            published_at,
            summary,
            content,
            ai_summary,
            score,
            score_reason,
            cve_list,
            category,
            created_at
        FROM articles
        WHERE UPPER(cve_list) ILIKE %s
        ORDER BY score DESC, published_at DESC NULLS LAST, created_at DESC
        LIMIT %s OFFSET %s
    """

    try:
        cursor.execute(query, (f"%{normalized_cve}%", limit, offset))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def delete_old_articles(days: int = 30) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = """
        DELETE FROM articles
        WHERE COALESCE(published_at, created_at) < %s
    """

    try:
        cursor.execute(query, (cutoff,))
        deleted_count = cursor.rowcount
        conn.commit()
        logger.info(f"Cleanup finished deleted={deleted_count} days={days}")
        return deleted_count
    finally:
        cursor.close()
        conn.close()


def get_stats():
    conn = get_dict_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) AS total_articles FROM articles")
        total_articles = cursor.fetchone()["total_articles"]

        cursor.execute("""
            SELECT score, COUNT(*) AS count
            FROM articles
            GROUP BY score
            ORDER BY score DESC
        """)
        score_distribution = cursor.fetchall()

        cursor.execute("""
            SELECT category, COUNT(*) AS count
            FROM articles
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
        """)
        top_categories = cursor.fetchall()

        cursor.execute("""
            SELECT source, COUNT(*) AS count
            FROM articles
            GROUP BY source
            ORDER BY count DESC
            LIMIT 10
        """)
        top_sources = cursor.fetchall()

        cursor.execute("""
            SELECT TRIM(value) AS cve, COUNT(*) AS count
            FROM articles,
            LATERAL unnest(string_to_array(cve_list, ',')) AS value
            WHERE cve_list IS NOT NULL AND cve_list <> ''
            GROUP BY TRIM(value)
            ORDER BY count DESC
            LIMIT 10
        """)
        top_cves = cursor.fetchall()

        cursor.execute("""
            SELECT
                id,
                title,
                link,
                source,
                published_at,
                summary,
                content,
                ai_summary,
                score,
                score_reason,
                cve_list,
                category,
                created_at
            FROM articles
            WHERE score >= 4
            ORDER BY score DESC, published_at DESC NULLS LAST, created_at DESC
            LIMIT 10
        """)
        top_threats = cursor.fetchall()

        return {
            "total_articles": total_articles,
            "score_distribution": score_distribution,
            "top_categories": top_categories,
            "top_sources": top_sources,
            "top_cves": top_cves,
            "top_threats": top_threats,
        }
    finally:
        cursor.close()
        conn.close()
