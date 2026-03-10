from contextlib import asynccontextmanager
from fastapi import FastAPI

from .localizer import Localizer
from ..services.events import SaveEventsService
from ..services.analytics import AnalyticsUsageService, AnalyticsSummaryService
from ..services.healthcheck import DatabaseHealthcheckService
from ..services.auth import (
    AnonymousService,
    LoginService,
    OAuthAuthorizeService,
    RefreshTokensService,
    RegisterService,
    ResendVerificationCodeService,
    SessionService,
    OAuthCallbackService,
    VerifyEmailService,
)
from ..services.email import EmailService
from ..services.user import (
    ProfileService,
    UpdateEmailService,
    UpdateUsernameService,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Асинхронная функция контекстного менеджера жизненного цикла приложения.

    Args:
        app: Экземпляр FastAPI-приложения.
    """
    # Localizer
    app.state.localizer = Localizer()  # type: ignore[attr-defined]
    # Healthcheck service
    app.state.database_healthcheck_service = DatabaseHealthcheckService()  # type: ignore[attr-defined]
    # Auth services
    app.state.anonymous_service = AnonymousService()  # type: ignore[attr-defined]
    app.state.register_service = RegisterService()  # type: ignore[attr-defined]
    app.state.login_service = LoginService()  # type: ignore[attr-defined]
    app.state.oauth_authorize_service = OAuthAuthorizeService()  # type: ignore[attr-defined]
    app.state.oauth_callback_service = OAuthCallbackService()  # type: ignore[attr-defined]
    app.state.refresh_tokens_service = RefreshTokensService()  # type: ignore[attr-defined]
    app.state.resend_verification_code_service = ResendVerificationCodeService()  # type: ignore[attr-defined]
    app.state.verify_email_service = VerifyEmailService()  # type: ignore[attr-defined]
    app.state.session_service = SessionService()  # type: ignore[attr-defined]
    # Email service (используется user- и auth-сервисами)
    app.state.email_service = EmailService()  # type: ignore[attr-defined]
    # User services
    app.state.profile_service = ProfileService()  # type: ignore[attr-defined]
    app.state.update_username_service = UpdateUsernameService()  # type: ignore[attr-defined]
    app.state.update_email_service = UpdateEmailService(email_service=app.state.email_service)  # type: ignore[attr-defined]
    # Events service
    app.state.save_events_service = SaveEventsService()  # type: ignore[attr-defined]
    # Analytics service
    app.state.analytics_usage_service = AnalyticsUsageService()  # type: ignore[attr-defined]
    app.state.analytics_summary_service = AnalyticsSummaryService()  # type: ignore[attr-defined]
    yield
