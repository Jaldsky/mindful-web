"""Константы путей API endpoints."""

API_V1_PREFIX = "/api/v1"

# Healthcheck
HEALTHCHECK_PATH = f"{API_V1_PREFIX}/healthcheck"

# Auth
AUTH_PATH = f"{API_V1_PREFIX}/auth"
AUTH_REGISTER_PATH = f"{AUTH_PATH}/register"
AUTH_LOGIN_PATH = f"{AUTH_PATH}/login"
AUTH_REFRESH_PATH = f"{AUTH_PATH}/refresh"
AUTH_VERIFY_PATH = f"{AUTH_PATH}/verify"
AUTH_RESEND_CODE_PATH = f"{AUTH_PATH}/resend-code"
AUTH_LOGOUT_PATH = f"{AUTH_PATH}/logout"
AUTH_ANONYMOUS_PATH = f"{AUTH_PATH}/anonymous"
AUTH_SESSION_PATH = f"{AUTH_PATH}/session"
# Oauth
AUTH_OAUTH_PATH = f"{AUTH_PATH}/oauth"
AUTH_OAUTH_CALLBACK_PATH = f"{AUTH_OAUTH_PATH}/{{provider}}/callback"
AUTH_OAUTH_AUTHORIZE_PATH = f"{AUTH_OAUTH_PATH}/{{provider}}/authorize"

# User
USER_PATH = f"{API_V1_PREFIX}/user"
USER_PROFILE_PATH = f"{USER_PATH}/profile"
USER_PROFILE_USERNAME_PATH = f"{USER_PROFILE_PATH}/username"
USER_PROFILE_EMAIL_PATH = f"{USER_PROFILE_PATH}/email"

# Events
EVENTS_PATH = f"{API_V1_PREFIX}/events"
SEND_EVENTS_PATH = f"{EVENTS_PATH}/save"

# Analytics
ANALYTICS_USAGE_PATH = f"{API_V1_PREFIX}/analytics/usage"
ANALYTICS_SUMMARY_PATH = f"{API_V1_PREFIX}/analytics/summary"
