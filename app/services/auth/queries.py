from datetime import datetime

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..types import Email, UserId, VerificationCode, Username
from .types import OAuthProviderName, OAuthProviderSubject
from ...db.models.tables import User, VerificationCode as VerificationCodeModel


async def fetch_users_by_username_or_email(session: AsyncSession, username: Username, email: Email) -> list[User]:
    """Функция получения пользователей по username или email.

    Args:
        session: AsyncSession.
        username: Username пользователя.
        email: Email пользователя.

    Returns:
        Пустой список или список найденных пользователей.
    """
    result = await session.execute(
        select(User).where(
            and_(
                User.deleted_at.is_(None),
                or_(User.username == username, User.email == email),
            )
        )
    )
    return list(result.scalars().all())


async def fetch_user_by_email(session: AsyncSession, email: Email) -> User | None:
    """Функция получения пользователя по email.

    Args:
        session: AsyncSession.
        email: Email пользователя.

    Returns:
        Пользователь или None, если не найден.
    """
    result = await session.execute(select(User).where(and_(User.email == email, User.deleted_at.is_(None))))
    return result.scalar_one_or_none()


async def fetch_user_by_email_or_pending(session: AsyncSession, email: Email) -> User | None:
    """Функция получения пользователя по email или pending_email.

    Args:
        session: AsyncSession.
        email: Email пользователя.

    Returns:
        Пользователь или None, если не найден.
    """
    result = await session.execute(
        select(User).where(
            and_(
                User.deleted_at.is_(None),
                or_(User.email == email, User.pending_email == email),
            )
        )
    )
    return result.scalar_one_or_none()


async def fetch_user_by_email_any_status(session: AsyncSession, email: Email) -> User | None:
    """Функция получения пользователя по email в любом статусе (включая soft-deleted).

    Args:
        session: AsyncSession.
        email: Email пользователя.

    Returns:
        Пользователь или None, если не найден.
    """
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def fetch_user_by_oauth_provider_subject_any_status(
    session: AsyncSession, provider: OAuthProviderName, provider_subject: OAuthProviderSubject
) -> User | None:
    """Функция получения пользователя по OAuth-провайдеру и subject в любом статусе.

    Args:
        session: AsyncSession.
        provider: OAuth-провайдер.
        provider_subject: Уникальный идентификатор пользователя у провайдера.

    Returns:
        Пользователь или None, если не найден.
    """
    result = await session.execute(
        select(User).where(
            and_(
                User.oauth_provider == provider,
                User.oauth_provider_subject == provider_subject,
            )
        )
    )
    return result.scalar_one_or_none()


async def fetch_user_by_id(session: AsyncSession, user_id: UserId) -> User | None:
    """Функция получения пользователя по user_id.

    Args:
        session: AsyncSession.
        user_id: ID пользователя.

    Returns:
        Пользователь или None, если не найден.
    """
    result = await session.execute(select(User).where(and_(User.id == user_id, User.deleted_at.is_(None))))
    return result.scalar_one_or_none()


async def fetch_user_by_username(session: AsyncSession, username: Username) -> User | None:
    """Функция получения пользователя по username.

    Args:
        session: AsyncSession.
        username: Username пользователя.

    Returns:
        Пользователь или None, если не найден.
    """
    result = await session.execute(select(User).where(and_(User.username == username, User.deleted_at.is_(None))))
    return result.scalar_one_or_none()


async def fetch_taken_usernames_any_status(session: AsyncSession, usernames: list[Username]) -> set[Username]:
    """Функция получения занятых username в любом статусе (включая soft-deleted).

    Args:
        session: AsyncSession.
        usernames: Список username-кандидатов для проверки.

    Returns:
        Множество занятых username из переданного списка.
    """
    if not usernames:
        return set()

    result = await session.execute(
        select(User.username).where(
            and_(
                User.username.is_not(None),
                User.username.in_(usernames),
            )
        )
    )
    return {u for u in result.scalars().all() if u is not None}


async def fetch_active_verification_code_row(
    session: AsyncSession, user_id: UserId, now: datetime
) -> VerificationCodeModel | None:
    """Функция получения активного кода подтверждения пользователя.

    Args:
        session: AsyncSession.
        user_id: ID пользователя.
        now: Текущее время (UTC).

    Returns:
        Активная запись кода или None.
    """
    result = await session.execute(
        select(VerificationCodeModel)
        .where(
            and_(
                VerificationCodeModel.user_id == user_id,
                VerificationCodeModel.used_at.is_(None),
                VerificationCodeModel.expires_at > now,
            )
        )
        .order_by(VerificationCodeModel.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def fetch_user_with_active_verification_code_by_email(
    session: AsyncSession, email: Email, now: datetime
) -> tuple[User | None, VerificationCodeModel | None]:
    """Функция получения пользователя по email или pending_email и активного кода подтверждения одним запросом.

    Активный код определяется как:
    - used_at IS NULL
    - expires_at > now
    Берётся самая свежая запись по created_at (DESC).

    Args:
        session: AsyncSession.
        email: Email пользователя.
        now: Текущее время (UTC).

    Returns:
        Кортеж (user, verification_code_row):
        - user: User или None, если пользователь не найден/удалён.
        - verification_code_row: Активная запись VerificationCodeModel или None, если активного кода нет.
    """
    result = await session.execute(
        select(User, VerificationCodeModel)
        .outerjoin(
            VerificationCodeModel,
            and_(
                VerificationCodeModel.user_id == User.id,
                VerificationCodeModel.used_at.is_(None),
                VerificationCodeModel.expires_at > now,
            ),
        )
        .where(
            and_(
                User.deleted_at.is_(None),
                or_(User.email == email, User.pending_email == email),
            )
        )
        .order_by(VerificationCodeModel.created_at.desc().nullslast())
        .limit(1)
    )
    row = result.first()
    if not row:
        return None, None
    user, code_row = row
    return user, code_row


async def fetch_latest_unused_verification_code_row(
    session: AsyncSession, user_id: UserId
) -> VerificationCodeModel | None:
    """Функция получения последней (по времени создания) неиспользованной записи кода подтверждения.

    В отличие от fetch_active_verification_code_row, не фильтрует по expires_at,
    чтобы можно было корректно различать "код истёк" и "кода нет".

    Args:
        session: AsyncSession.
        user_id: ID пользователя.

    Returns:
        Последняя запись кода или None.
    """
    result = await session.execute(
        select(VerificationCodeModel)
        .where(
            and_(
                VerificationCodeModel.user_id == user_id,
                VerificationCodeModel.used_at.is_(None),
            )
        )
        .order_by(VerificationCodeModel.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def fetch_user_with_latest_unused_verification_code_by_email(
    session: AsyncSession, email: Email
) -> tuple[User | None, VerificationCodeModel | None]:
    """Функция получения пользователя по email или pending_email и последней неиспользованной записи кода одним запросом.

    Последняя неиспользованная запись определяется как:
    - used_at IS NULL
    Берётся самая свежая запись по created_at (DESC).

    Важно: expires_at намеренно НЕ фильтруется, чтобы на уровне use-case можно было отличать:
    - "кода нет" (None)
    - "код есть, но истёк"

    Args:
        session: AsyncSession.
        email: Email пользователя.

    Returns:
        Кортеж (user, verification_code_row):
        - user: User или None, если пользователь не найден/удалён.
        - verification_code_row: Последняя запись VerificationCodeModel (used_at IS NULL) или None.
    """
    result = await session.execute(
        select(User, VerificationCodeModel)
        .outerjoin(
            VerificationCodeModel,
            and_(
                VerificationCodeModel.user_id == User.id,
                VerificationCodeModel.used_at.is_(None),
            ),
        )
        .where(
            and_(
                User.deleted_at.is_(None),
                or_(User.email == email, User.pending_email == email),
            )
        )
        .order_by(VerificationCodeModel.created_at.desc().nullslast())
        .limit(1)
    )
    row = result.first()
    if not row:
        return None, None
    user, code_row = row
    return user, code_row


async def fetch_user_with_latest_verification_code_by_email(
    session: AsyncSession, email: Email
) -> tuple[User | None, VerificationCodeModel | None]:
    """Функция получения пользователя по email или pending_email и последней записи кода одним запросом.

    Args:
        session: AsyncSession.
        email: Email пользователя.

    Returns:
        Кортеж (user, verification_code_row)
    """
    result = await session.execute(
        select(User, VerificationCodeModel)
        .outerjoin(
            VerificationCodeModel,
            VerificationCodeModel.user_id == User.id,
        )
        .where(
            and_(
                User.deleted_at.is_(None),
                or_(User.email == email, User.pending_email == email),
            )
        )
        .order_by(VerificationCodeModel.created_at.desc().nullslast())
        .limit(1)
    )
    row = result.first()
    if not row:
        return None, None
    user, code_row = row
    return user, code_row


async def fetch_unused_verification_code_row_by_user_and_code(
    session: AsyncSession, user_id: UserId, code: VerificationCode
) -> VerificationCodeModel | None:
    """Функция получения кода подтверждения по user_id и code.

    Args:
        session: AsyncSession.
        user_id: ID пользователя.
        code: Код подтверждения.

    Returns:
        Запись кода или None, если не найдена.
    """
    result = await session.execute(
        select(VerificationCodeModel)
        .where(
            and_(
                VerificationCodeModel.user_id == user_id,
                VerificationCodeModel.code == code,
                VerificationCodeModel.used_at.is_(None),
            )
        )
        .order_by(VerificationCodeModel.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def update_verification_code_last_sent_at(
    session: AsyncSession, verification_code_id: int, at: datetime
) -> None:
    """Функция обновления времени последней отправки кода (last_sent_at).

    Args:
        session: AsyncSession.
        verification_code_id: ID записи кода в таблице verification_codes.
        at: Время обновления (UTC).
    """
    await session.execute(
        update(VerificationCodeModel).where(VerificationCodeModel.id == verification_code_id).values(last_sent_at=at)
    )
