import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OAuthProviderConfig:
    """Конфиг одного OAuth-провайдера."""

    provider: str
    client_id: str
    client_secret: str
    redirect_uri: str
    auth_url: str
    auth_scope: str
    token_url: str
    tokeninfo_url: str
    allowed_issuers: tuple[str, ...]


_GOOGLE_OAUTH_CLIENT_ID: str = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
_GOOGLE_OAUTH_CLIENT_SECRET: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
_GOOGLE_OAUTH_REDIRECT_URI: str = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "")

OAUTH_PROVIDER_CONFIGS: dict[str, OAuthProviderConfig] = {}
if _GOOGLE_OAUTH_CLIENT_ID and _GOOGLE_OAUTH_CLIENT_SECRET and _GOOGLE_OAUTH_REDIRECT_URI:
    OAUTH_PROVIDER_CONFIGS["google"] = OAuthProviderConfig(
        provider="google",
        client_id=_GOOGLE_OAUTH_CLIENT_ID,
        client_secret=_GOOGLE_OAUTH_CLIENT_SECRET,
        redirect_uri=_GOOGLE_OAUTH_REDIRECT_URI,
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        auth_scope="openid email profile",
        token_url="https://oauth2.googleapis.com/token",
        tokeninfo_url="https://oauth2.googleapis.com/tokeninfo",
        allowed_issuers=("https://accounts.google.com", "accounts.google.com"),
    )
