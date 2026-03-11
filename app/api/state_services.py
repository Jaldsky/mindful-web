from fastapi import Request


def get_database_healthcheck_service(request: Request):
    """Возвращает сервис проверки доступности БД.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр DatabaseHealthcheckService.
    """
    return request.app.state.database_healthcheck_service


def get_save_events_service(request: Request):
    """Возвращает сервис сохранения событий.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр SaveEventsService.
    """
    return request.app.state.save_events_service


def get_analytics_domains_service(request: Request):
    """Возвращает сервис доменной аналитики по доменам.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр AnalyticsDomainsService.
    """
    return request.app.state.analytics_domains_service


def get_analytics_summary_service(request: Request):
    """Возвращает сервис summary аналитики использования по доменам.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр AnalyticsSummaryService.
    """
    return request.app.state.analytics_summary_service


def get_anonymous_service(request: Request):
    """Возвращает сервис создания анонимной сессии.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр AnonymousService.
    """
    return request.app.state.anonymous_service


def get_register_service(request: Request):
    """Возвращает сервис регистрации пользователя.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр RegisterService.
    """
    return request.app.state.register_service


def get_login_service(request: Request):
    """Возвращает сервис авторизации.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр LoginService.
    """
    return request.app.state.login_service


def get_oauth_callback_service(request: Request):
    """Возвращает сервис обработки OAuth callback.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр OAuthCallbackService.
    """
    return request.app.state.oauth_callback_service


def get_oauth_authorize_service(request: Request):
    """Возвращает сервис OAuth authorize (редирект к провайдеру).

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр OAuthAuthorizeService.
    """
    return request.app.state.oauth_authorize_service


def get_refresh_tokens_service(request: Request):
    """Возвращает сервис обновления пары access и refresh токенов.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр RefreshTokensService.
    """
    return request.app.state.refresh_tokens_service


def get_resend_verification_code_service(request: Request):
    """Возвращает сервис повторной отправки кода подтверждения на email.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр ResendVerificationCodeService.
    """
    return request.app.state.resend_verification_code_service


def get_verify_email_service(request: Request):
    """Возвращает сервис подтверждения email по коду из письма.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр VerifyEmailService.
    """
    return request.app.state.verify_email_service


def get_session_service(request: Request):
    """Возвращает сервис проверки текущей сессии (access/anon по cookies).

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр SessionService.
    """
    return request.app.state.session_service


def get_profile_service(request: Request):
    """Возвращает сервис получения профиля текущего пользователя.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр ProfileService.
    """
    return request.app.state.profile_service


def get_update_username_service(request: Request):
    """Возвращает сервис обновления логина текущего пользователя.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр UpdateUsernameService.
    """
    return request.app.state.update_username_service


def get_update_email_service(request: Request):
    """Возвращает сервис обновления email текущего пользователя.

    Args:
        request: HTTP-запрос.

    Returns:
        Экземпляр UpdateEmailService.
    """
    return request.app.state.update_email_service
