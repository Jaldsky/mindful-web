import os

POSTGRES_USER: str = os.getenv("POSTGRES_USER", "root")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "root")
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "mindfulweb")

DATABASE_URL: str = os.getenv(
    "DATABASE_URL", f"postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}"
)
REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
