BEGIN;

CREATE INDEX IF NOT EXISTS idx_articles_published_at_desc
ON articles (published_at DESC);

CREATE INDEX IF NOT EXISTS idx_articles_created_at_desc
ON articles (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_articles_score_published_at
ON articles (score DESC, published_at DESC);

CREATE INDEX IF NOT EXISTS idx_articles_category
ON articles (category);

CREATE INDEX IF NOT EXISTS idx_articles_source
ON articles (source);

CREATE INDEX IF NOT EXISTS idx_articles_coalesce_pub_created
ON articles ((COALESCE(published_at, created_at)));

COMMIT;
