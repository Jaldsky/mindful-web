import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    Boolean,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import CreatedMixin, UpdatedMixin, DeletedMixin


class User(Base, CreatedMixin, UpdatedMixin, DeletedMixin):
    """Таблица пользователей системы."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор пользователя (UUID4)",
    )
    username: Mapped[str | None] = Column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        comment="Логин пользователя",
    )
    email: Mapped[str | None] = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        comment="Email для авторизации",
    )
    pending_email: Mapped[str | None] = Column(
        String(255),
        unique=False,
        nullable=True,
        index=True,
        comment="Новый email для подтверждения",
    )
    password: Mapped[str | None] = Column(String(255), nullable=True, comment="Хэш пароля")
    oauth_provider: Mapped[str | None] = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Внешний OAuth провайдер",
    )
    oauth_provider_subject: Mapped[str | None] = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        comment="Идентификатор пользователя у внешнего OAuth провайдера",
    )
    is_verified: Mapped[bool] = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Подтверждён ли email пользователя",
    )

    attention_events: Mapped[list["AttentionEvent"]] = relationship(
        "AttentionEvent", back_populates="user", cascade="all, delete-orphan"
    )
    verification_codes: Mapped[list["VerificationCode"]] = relationship(
        "VerificationCode", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class VerificationCode(Base, CreatedMixin):
    """Таблица кодов подтверждения email."""

    __tablename__ = "verification_codes"

    id: Mapped[int] = Column(Integer, primary_key=True, comment="Автоинкрементный ID кода")
    user_id: Mapped[uuid.UUID] = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="ID пользователя",
    )
    code: Mapped[str] = Column(
        String(6),
        nullable=False,
        comment="Код подтверждения",
    )
    attempts: Mapped[int] = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Количество неудачных попыток ввода кода",
    )
    expires_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Время истечения кода (UTC)",
    )
    used_at: Mapped[datetime | None] = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время использования кода (UTC)",
    )
    last_sent_at: Mapped[datetime | None] = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время последней отправки кода (UTC)",
    )

    user: Mapped["User"] = relationship("User", back_populates="verification_codes")

    __table_args__ = (Index("idx_verification_codes_user_code", "user_id", "code"),)

    def __repr__(self) -> str:
        return f"<VerificationCode(id={self.id}, user_id={self.user_id}, code={self.code[:2]}**)>"


class DomainCategory(Base, CreatedMixin, UpdatedMixin):
    """Таблица категорий цифровой активности."""

    __tablename__ = "domain_categories"

    id: Mapped[int] = Column(Integer, primary_key=True, comment="Автоинкрементный ID категории")
    name: Mapped[str] = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Уникальное имя категории",
    )

    domain_to_category: Mapped[list["DomainToCategory"]] = relationship(
        "DomainToCategory", back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DomainCategory(id={self.id}, name={self.name})>"


class DomainToCategory(Base, CreatedMixin, UpdatedMixin):
    """Таблица связи домена с цифровой активностью."""

    __tablename__ = "domain_to_category"

    domain: Mapped[str] = Column(
        String(255),
        primary_key=True,
        comment="Домен в нижнем регистре (например: 'instagram.com')",
    )
    category_id: Mapped[int] = Column(
        Integer,
        ForeignKey("domain_categories.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="Ссылка на категорию из таблицы domain_categories",
    )

    category: Mapped["DomainCategory"] = relationship("DomainCategory", back_populates="domain_to_category")

    def __repr__(self) -> str:
        return f"<DomainToCategory(domain={self.domain}, category_id={self.category_id})>"


class AttentionEvent(Base):
    """Таблица событий внимания от расширения."""

    __tablename__ = "attention_events"

    id: Mapped[int] = Column(Integer, primary_key=True, comment="Автоинкрементный ID события")
    user_id: Mapped[uuid.UUID] = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="ID пользователя",
    )
    domain: Mapped[str] = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Домен",
    )
    event_type: Mapped[str] = Column(
        String(10),
        nullable=False,
        comment="Тип события внимания: active (пользователь перешёл на вкладку) или inactive (покинул вкладку)",
    )
    timestamp: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Точное время события в UTC",
    )

    user: Mapped["User"] = relationship("User", back_populates="attention_events")

    __table_args__ = (
        CheckConstraint(
            text("event_type IN ('active', 'inactive')"),
            name="valid_attention_event_type",
        ),
        Index("idx_attention_events_user_domain_timestamp", "user_id", "domain", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<AttentionEvent(id={self.id}, user_id={self.user_id}, "
            f"domain={self.domain}, event_type={self.event_type})>"
        )
