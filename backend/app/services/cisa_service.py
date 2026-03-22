import requests
from datetime import datetime, timedelta
from app.core.logging import setup_logger

logger = setup_logger("cyhackt.cisa")

CISA_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
MAX_CISA_DAYS = 30
REQUEST_TIMEOUT = 15


def is_recent(date_str: str, max_days: int = MAX_CISA_DAYS) -> bool:
    if not date_str:
        return False

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return False

    cutoff = datetime.utcnow() - timedelta(days=max_days)
    return date_obj >= cutoff


def is_valid_cisa_article(article: dict) -> bool:
    title = (article.get("title") or "").strip()
    link = (article.get("link") or "").strip()
    content = (article.get("content") or "").strip()

    return bool(title and link and content)


def fetch_cisa_articles(include_history: bool = False) -> list[dict]:
    logger.info(f"CISA ingestion started include_history={include_history}")

    try:
        response = requests.get(CISA_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.exception(f"CISA request failed error={str(e)}")
        return []

    articles = []
    total_items = len(data.get("vulnerabilities", []))
    skipped_old = 0
    skipped_invalid = 0

    logger.info(f"CISA payload received entries={total_items}")

    for item in data.get("vulnerabilities", []):
        cve_id = (item.get("cveID") or "").strip()
        vendor = (item.get("vendorProject") or "").strip()
        product = (item.get("product") or "").strip()
        vuln_name = (item.get("vulnerabilityName") or "").strip()
        date_added = (item.get("dateAdded") or "").strip()
        required_action = (item.get("requiredAction") or "").strip()
        ransomware_use = (item.get("knownRansomwareCampaignUse") or "").strip()

        if not include_history and not is_recent(date_added):
            skipped_old += 1
            continue

        title_parts = [cve_id, vuln_name]
        title = " - ".join([part for part in title_parts if part]).strip()

        summary_parts = [
            f"Vendor: {vendor}" if vendor else "",
            f"Product: {product}" if product else "",
            f"Required action: {required_action}" if required_action else "",
            f"Known ransomware use: {ransomware_use}" if ransomware_use else "",
        ]
        summary = " | ".join([part for part in summary_parts if part])

        content = " ".join(
            part for part in [
                "CISA Known Exploited Vulnerability.",
                f"CVE: {cve_id}." if cve_id else "",
                f"Vendor: {vendor}." if vendor else "",
                f"Product: {product}." if product else "",
                f"Vulnerability: {vuln_name}." if vuln_name else "",
                f"Date added: {date_added}." if date_added else "",
                f"Required action: {required_action}." if required_action else "",
                f"Known ransomware campaign use: {ransomware_use}." if ransomware_use else "",
            ]
            if part
        ).strip()

        article = {
            "title": title or cve_id or "CISA KEV Entry",
            "link": (
                f"https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
                f"?search_api_fulltext={cve_id}"
                if cve_id
                else "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
            ),
            "source": "CISA",
            "published_at": date_added,
            "summary": summary,
            "content": content,
        }

        if not is_valid_cisa_article(article):
            skipped_invalid += 1
            continue

        articles.append(article)

    logger.info(
        f"CISA ingestion finished kept={len(articles)} "
        f"skipped_old={skipped_old} skipped_invalid={skipped_invalid}"
    )

    return articles
