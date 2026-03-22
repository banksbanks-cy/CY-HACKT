from app.services.rss_service import fetch_articles

articles = fetch_articles()

print(f"Nombre d'articles: {len(articles)}")

for article in articles[:3]:
    print(article["title"])
    print(article["source"])
    print(article["link"])
    print("-" * 40)
