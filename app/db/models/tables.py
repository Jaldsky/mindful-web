import uuid
from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import Base


class User(Base):
    """Таблица пользователей системы."""

    __tablename__ = "users"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор пользователя (UUID4)",
    )
    email = Column(
        String(255), unique=True, nullable=True, comment="Email для авторизации (может быть NULL для анонимов)"
    )
    password = Column(
        String(255), nullable=True, comment="Хэш пароля (bcrypt/scrypt); NULL для анонимных пользователей"
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default="now()", comment="Время регистрации (UTC)"
    )
    deleted_at = Column(
        DateTime(timezone=True), nullable=True, comment="Время soft-delete (если не NULL — пользователь удалён)"
    )


class DomainCategory(Base):
    """Таблица категорий цифровой активности."""

    __tablename__ = "domain_categories"

    id = Column(Integer, primary_key=True, comment="Автоинкрементный ID категории")
    name = Column(
        String(50), unique=True, nullable=False, comment="Уникальное имя категории (например: 'entertainment', 'work')"
    )


class DomainCategoryMapping(Base):
    """Таблица связи домена с цифровой активностью."""

    __tablename__ = "domain_category_mapping"

    domain = Column(
        String(255), primary_key=True, comment="Домен в нижнем регистре без www (например: 'instagram.com')"
    )
    category_id = Column(
        Integer,
        ForeignKey("domain_categories.id"),
        nullable=False,
        comment="Ссылка на категорию из таблицы domain_categories",
    )


class AttentionEvent(Base):
    """Таблица событий."""

    __tablename__ = "attention_events"

    id = Column(Integer, primary_key=True, comment="Автоинкрементный ID события")
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="ID пользователя, которому принадлежит событие",
    )
    domain = Column(String(255), nullable=False, comment="Домен, на котором произошло событие")
    event_type = Column(String(10), nullable=False, comment="Тип события: 'focus' или 'blur'")
    timestamp = Column(DateTime(timezone=True), nullable=False, comment="Точное время события в UTC (от браузера)")

    __table_args__ = (CheckConstraint(event_type.in_(["focus", "blur"]), name="valid_event_type"),)


class DailyDomainSummary(Base):
    """Таблица агрегированного отчета на домене за день."""

    __tablename__ = "daily_domain_summaries"

    id = Column(Integer, primary_key=True, comment="Автоинкрементный ID записи")
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="ID пользователя")
    domain = Column(String(255), nullable=False, comment="Домен, по которому собрана статистика")
    date = Column(Date, nullable=False, comment="Дата отчёта (без времени, в UTC)")
    total_seconds = Column(
        Integer, nullable=False, comment="Суммарное время пребывания в секундах (только по завершённым сессиям)"
    )
    focus_count = Column(Integer, nullable=False, comment="Количество фокусировок на домене за день")
    generated_at = Column(
        DateTime(timezone=True), nullable=False, server_default="now()", comment="Время генерации отчёта (UTC)"
    )
