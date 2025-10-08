import logging
from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .exceptions import EventsServiceException, EventsServiceMessages
from ...db.models.tables import AttentionEvent, User
from ...schemas.events.send_events_request_schema import SendEventsRequestSchema, SendEventData

logger = logging.getLogger(__name__)


class EventsServiceBase(ABC):
    """Базовый класс сервиса событий."""

    exception = EventsServiceException
    messages = EventsServiceMessages

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация класса.

        Args:
            session: Сессия с базой данных.
        """
        self.session = session

    @abstractmethod
    async def exec(self, *args, **kwargs):
        """Метод выполнения основной логики."""


class EventsService(EventsServiceBase):
    """Класс сервиса событий."""

    async def _ensure_user_exists(self, user_id: UUID) -> None:
        """Метод получение или создание пользователя в базе данных.

        Args:
            user_id: Идентификатор пользователя.
        """
        try:
            user_insert = insert(User).values(id=user_id).on_conflict_do_nothing(index_elements=["id"])
            await self.session.execute(user_insert)
        except Exception as e:
            logger.error(f"Failed to ensure user {user_id} exists: {e.__str__()}")
            raise self.exception(self.messages.GET_OR_CREATE_USER_ERROR.format(user_id=user_id)) from e

    async def _insert_events(self, events: list[SendEventData], user_id: UUID) -> None:
        """Метод добавления событий в базу данных.

        Args:
            events: Список событий.
            user_id: Идентификатор пользователя.
        """
        try:
            events = [
                AttentionEvent(
                    user_id=user_id,
                    domain=event.domain,
                    event_type=event.event,
                    timestamp=event.timestamp,
                )
                for event in events
            ]
            self.session.add_all(events)
        except Exception as e:
            logger.error(f"Failed to prepare events for user {user_id}: {e}")
            raise self.exception(self.messages.ADD_EVENTS_ERROR)

    async def exec(self, events: SendEventsRequestSchema, user_id: UUID) -> None:
        """Метод выполнения основной логики.

        Args:
            events: Модель событий.
            user_id: Идентификатор пользователоя.
        """
        try:
            await self._ensure_user_exists(user_id)
            await self._insert_events(events.data, user_id)
            await self.session.commit()
            logger.info(f"Successfully processed {len(events.data)} events for user {user_id}")
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error while processing events for user {user_id}: {e}")
            raise self.exception(self.messages.DATA_INTEGRITY_ERROR) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error while processing events for user {user_id}: {e}")
            raise self.exception(self.messages.DATA_SAVE_ERROR) from e
        except EventsServiceException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Unexpected error while processing events for user {user_id}: {e}")
            raise self.exception(self.messages.UNEXPECTED_ERROR) from e
