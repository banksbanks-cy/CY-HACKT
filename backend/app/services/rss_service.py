import feedparser
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from app.utils.text_cleaner import clean_html
from app.core.logging import setup_logger

logger = setup_logger("cyhackt.rss")

RSS_FEEDS = [
    {
        "name": "TheHackersNews",
        "url": "https://feeds.feedburner.com/TheHackersNews",
    },
    {
        "name": "BleepingComputer",
        "url": "https://www.bleepingcomputer.com/feed/",
    },
    {
        "name": "GitHubAdvisories",
        "url": "https://github.com/advisories.atom",
    },
]

MAX_ARTICLES_PER_FEED = 30
MAX_ARTICLE_AGE_DAYS = 30
MIN_TEXT_LENGTH = 80


def extract_content(entry):
    if "content" in entry and len(entry.content) > 0:
        return clean_html(entry.content[0].value)

    if hasattr(entry, "description"):
        return clean_html(entry.description)

    if hasattr(entry, "summary"):
        return clean_html(entry.summary)

    return ""


def parse_entry_date(entry):
    date_value = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if not date_value:
        return None

    try:
        dt = parsedate_to_datetime(date_value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def is_recent_enough(entry, max_age_days=MAX_ARTICLE_AGE_DAYS):
    entry_date = parse_entry_date(entry)
    if entry_date is None:
        return True

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max_age_days)
    return entry_date >= cutoff


def is_valid_article(article: dict) -> bool:
    title = (article.get("title") or "").strip()
    link = (article.get("link") or "").strip()
    summary = (article.get("summary") or "").strip()
    content = (article.get("content") or "").strip()

    if not title or not link:
        return False

    full_text = f"{title} {summary} {content}".strip()
    if len(full_text) < MIN_TEXT_LENGTH:
        return False

    return True


def fetch_articles():
    all_articles = []

    logger.info("RSS ingestion started")

    for feed_info in RSS_FEEDS:
        source_name = feed_info["name"]
        source_url = feed_info["url"]

        try:
            feed = feedparser.parse(source_url)

            if getattr(feed, "bozo", False):
                logger.warning(f"RSS source malformed but readable: source={source_name}")

            total_entries = len(feed.entries)
            kept_count = 0
            skipped_old = 0
            skipped_invalid = 0

            logger.info(f"Reading RSS source={source_name} entries={total_entries}")

            for entry in feed.entries:
                if kept_count >= MAX_ARTICLES_PER_FEED:
                    break

                if not is_recent_enough(entry):
                    skipped_old += 1
                    continue

                summary = clean_html(getattr(entry, "summary", ""))
                content = extract_content(entry)

                article = {
                    "title": getattr(entry, "title", "").strip(),
                    "link": getattr(entry, "link", "").strip(),
                    "source": source_name,
                    "published_at": getattr(entry, "published", None) or getattr(entry, "updated", None),
                    "summary": summary,
                    "content": content or summary,
                }

                if not is_valid_article(article):
                    skipped_invalid += 1
                    continue

                all_articles.append(article)
                kept_count += 1

            logger.info(
                f"RSS source done source={source_name} kept={kept_count} "
                f"skipped_old={skipped_old} skipped_invalid={skipped_invalid}"
            )

        except Exception as e:
            logger.exception(f"RSS source failed source={source_name} error={str(e)}")

    logger.info(f"RSS ingestion finished total_articles={len(all_articles)}")
    return all_articles
