from app.services.rss_service import fetch_articles
from app.services.article_service import save_articles

articles = fetch_articles()
result = save_articles(articles)

print(result)
