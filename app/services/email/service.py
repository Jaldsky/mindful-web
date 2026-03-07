import logging
from typing import Any

from ..types import Email, VerificationCode
from .constants import (
    VERIFICATION_CODE_TEMPLATE,
    VERIFICATION_EMAIL_SUBJECT,
)
from .types import FromName
from .builder import EmailMessageBuilder
from .renderer import TemplateRenderer, TemplateRendererSettings
from .smtp import EmailServiceSettings, SMTPTransport
from .normalizers import EmailServiceNormalizers
from .validators import EmailServiceValidators
from ...config import VERIFICATION_CODE_EXPIRE_MINUTES

logger = logging.getLogger(__name__)


class EmailService:
    """Сервис отправки email."""

    def __init__(
        self,
        *,
        settings: EmailServiceSettings | None = None,
        **overrides: Any,
    ) -> None:
        """Магический метод инициализации класса.

        Args:
            settings: Явно переданные настройки email-сервиса.
            **overrides: Переопределения полей настроек.
        """
        self._settings = settings or EmailServiceSettings.from_defaults(**overrides)
        self._renderer = TemplateRenderer(TemplateRendererSettings(templates_dir=self._settings.templates_dir))
        self._transport = SMTPTransport(self._settings)

    def _resolve_sender(
        self, from_email: Email | None = None, from_name: FromName | None = None
    ) -> tuple[Email, FromName]:
        """Метод разрешения данных отправителя.
        Использует переданные значения или значения по умолчанию из настроек.

        Args:
            from_email: Email адрес отправителя.
            from_name: Имя отправителя.

        Returns:
            Кортеж из email адреса и имени отправителя.
        """
        return (
            from_email or self._settings.from_email,
            from_name or self._settings.from_name,
        )

    async def send_verification_code(
        self,
        to_email: Email,
        code: VerificationCode,
        from_email: Email | None = None,
        from_name: FromName | None = None,
    ) -> None:
        """Метод отправки кода подтверждения на email.

        Процесс отправки включает:
        1. Нормализацию входных данных
        2. Валидацию формата всех полей
        3. Создание письма с кодом подтверждения используя шаблон
        4. Отправку письма через SMTP сервер

        Args:
            to_email: Email адрес получателя.
            code: Код подтверждения.
            from_email: Email адрес отправителя.
            from_name: Имя отправителя.

        Raises:
            InvalidEmailFormatException: При неверном формате email адреса.
            InvalidVerificationCodeException: При неверном формате кода подтверждения.
            EmailSendFailedException: При ошибке подключения, аутентификации или отправки email.
        """
        normalized_to: Email = EmailServiceNormalizers.normalize_email(to_email)
        EmailServiceValidators.validate_email(normalized_to)

        normalized_code: VerificationCode = EmailServiceNormalizers.normalize_verification_code(code)
        EmailServiceValidators.validate_verification_code(normalized_code)

        resolved_from_email, resolved_from_name = self._resolve_sender(from_email, from_name)
        normalized_sender: Email = EmailServiceNormalizers.normalize_email(resolved_from_email)
        if from_email is not None:
            EmailServiceValidators.validate_email(normalized_sender)

        html = self._renderer.render(
            VERIFICATION_CODE_TEMPLATE,
            context={"code": normalized_code, "expire_minutes": VERIFICATION_CODE_EXPIRE_MINUTES},
        )
        message = EmailMessageBuilder.build_html_message(
            to_email=normalized_to,
            subject=VERIFICATION_EMAIL_SUBJECT,
            html=html,
            from_email=normalized_sender,
            from_name=resolved_from_name,
        )

        await self._transport.send(
            message,
            sender=normalized_sender,
            recipient=normalized_to,
        )
        logger.info(f"Verification email sent to {normalized_to}")
