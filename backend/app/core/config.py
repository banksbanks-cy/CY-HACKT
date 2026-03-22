import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/cyhackt"
)

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
