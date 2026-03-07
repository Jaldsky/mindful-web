import os
from secrets import token_urlsafe

DATE_FORMATS = [
    "%d-%m-%Y",  # DD-MM-YYYY
    "%Y-%m-%d",  # YYYY-MM-DD
]

# Localization
DEFAULT_LOCALE = "en"
ACCEPT_LANGUAGE_HEADER = "Accept-Language"
SUPPORTED_LOCALES: tuple[str, ...] = ("en", "ru")

DEFAULT_PAGE_SIZE: int = 20

CORS_ALLOW_ORIGINS: list[str] = [x.strip() for x in (os.getenv("CORS_ALLOW_ORIGINS") or "").split(",") if x.strip()]

# Database
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "mwb-db")
POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", 5432)
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "mwb")
POSTGRES_USER: str = os.getenv("POSTGRES_USER", "root")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "root")

DATABASE_ASYNC_URL: str = os.getenv(
    "DATABASE_ASYNC_URL",
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
)
DATABASE_SYNC_URL: str = os.getenv(
    "DATABASE_SYNC_URL",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
)

# Redis
REDIS_HOST: str = os.getenv("REDIS_HOST", "mwb-redis")
REDIS_PORT: str = os.getenv("REDIS_PORT", 6379)
REDIS_DB: str = os.getenv("REDIS_DB", 0)
REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "root")

REDIS_URL: str = os.getenv("REDIS_URL", f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

# Email Configuration
SMTP_HOST: str = os.getenv("SMTP_HOST", "mwb-mailhog")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER: str = os.getenv("SMTP_USER", "root")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "root")

SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@mindful-web.com")
SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Mindful-Web")
SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "false").lower() == "true"

# Verification Code
VERIFICATION_CODE_EXPIRE_MINUTES: int = int(os.getenv("VERIFICATION_CODE_EXPIRE_MINUTES", "15"))
VERIFICATION_CODE_RESEND_COOLDOWN_SECONDS: int = int(os.getenv("VERIFICATION_CODE_RESEND_COOLDOWN_SECONDS", "60"))
VERIFICATION_CODE_REQUEST_COOLDOWN_SECONDS: int = int(os.getenv("VERIFICATION_CODE_REQUEST_COOLDOWN_SECONDS", "60"))
VERIFICATION_CODE_MAX_ATTEMPTS: int = int(os.getenv("VERIFICATION_CODE_MAX_ATTEMPTS", "10"))

# JWT Configuration
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", token_urlsafe(32))
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_ANON_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ANON_TOKEN_EXPIRE_MINUTES", "60"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Auth Cookies
AUTH_COOKIE_SECURE: bool = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
AUTH_COOKIE_HTTPONLY: bool = os.getenv("AUTH_COOKIE_HTTPONLY", "true").lower() == "true"
AUTH_COOKIE_DOMAIN: str = os.getenv("AUTH_COOKIE_DOMAIN", "")
AUTH_COOKIE_SAMESITE: str = os.getenv("AUTH_COOKIE_SAMESITE", "lax").lower()
OAUTH_STATE_COOKIE_EXPIRE_MINUTES: int = int(os.getenv("OAUTH_STATE_COOKIE_EXPIRE_MINUTES", "10"))
