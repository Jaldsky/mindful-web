import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Any, NoReturn
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ....schemas.analytics.timeline.response_ok_schema import (
    AnalyticsTimelineDomainData,
    AnalyticsTimelineDataPoint,
    AnalyticsTimelineResponseOkSchema,
)
from ....services.exceptions import ServiceDatabaseErrorException
from ..exceptions import AnalyticsServiceException
from ..queries import execute_usage_timeline_query
from ..types import Date, UsageTimelineRow, TimelineGranularity, TopDomainsLimit

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class ComputeUsageTimelineData:
    """Входные данные для вычисления timeline статистики использования."""

    user_id: UUID
    start_date: Date
    end_date: Date
    granularity: TimelineGranularity = "day"
    top_domains_limit: TopDomainsLimit = 5


class ComputeUsageTimelineServiceBase:
    """Базовый класс сервиса вычисления timeline статистики использования."""

    session: Session | AsyncSession
    _data: ComputeUsageTimelineData

    def __init__(self, session: Session | AsyncSession, **kwargs: Any) -> None:
        """Инициализация сервиса вычисления timeline статистики.

        Args:
            session: Sync или Async сессия SQLAlchemy.
            **kwargs: Аргументы для ComputeUsageTimelineData.
        """
        self.session = session
        self._data = ComputeUsageTimelineData(**kwargs)

    @property
    def user_id(self) -> UUID:
        """Свойство получения идентификатора пользователя.

        Returns:
            Идентификатор пользователя.
        """
        return self._data.user_id

    @property
    def start_date(self) -> Date:
        """Свойство получения даты начала периода.

        Returns:
            Дата начала периода.
        """
        return self._data.start_date

    @property
    def end_date(self) -> Date:
        """Свойство получения даты конца периода.

        Returns:
            Дата окончания периода.
        """
        return self._data.end_date

    @property
    def granularity(self) -> TimelineGranularity:
        """Свойство получения гранулярности агрегации.

        Returns:
            Гранулярность агрегации.
        """
        return self._data.granularity

    @property
    def top_domains_limit(self) -> TopDomainsLimit:
        """Свойство получения лимита доменов внутри бакета.

        Returns:
            Максимальное количество доменов в каждом временном бакете.
        """
        return self._data.top_domains_limit


class ComputeUsageTimelineService(ComputeUsageTimelineServiceBase):
    """Сервис вычисления timeline статистики активности пользователя."""

    @staticmethod
    def _build_time_range(start_date: Date, end_date: Date) -> tuple[datetime, datetime]:
        """Приватный метод построения временного диапазона по датам.

        Args:
            start_date: Дата начала периода.
            end_date: Дата окончания периода.

        Returns:
            Кортеж (start_dt, end_dt) в UTC.
        """
        start_dt = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)
        return start_dt, end_dt

    @staticmethod
    def _parse_domains(raw_domains: Any) -> list[AnalyticsTimelineDomainData]:
        """Парсит домены бакета из SQL поля domains.

        Поддерживаемые форматы:
        - JSON list (PostgreSQL json/jsonb) → list[dict]
        - JSON string → парсится через json.loads

        Args:
            raw_domains: Сырое значение поля domains из SQL.

        Returns:
            Нормализованный список AnalyticsTimelineDomainData.
        """
        if not raw_domains:
            return []
        if isinstance(raw_domains, str):
            import json

            try:
                raw_domains = json.loads(raw_domains)
            except Exception:
                return []
        if not isinstance(raw_domains, list):
            return []

        normalized: list[AnalyticsTimelineDomainData] = []
        for item in raw_domains:
            if not isinstance(item, dict):
                continue
            domain = item.get("domain")
            total_seconds = item.get("total_seconds", 0)
            if domain is None:
                continue
            normalized.append(
                AnalyticsTimelineDomainData(
                    domain=str(domain),
                    total_seconds=int(total_seconds or 0),
                )
            )
        return normalized

    async def _fetch_timeline(self, *, start_dt: datetime, end_dt: datetime) -> list[UsageTimelineRow]:
        """Приватный метод выполнения SQL-запроса timeline статистики.

        Args:
            start_dt: Начальный datetime (UTC).
            end_dt: Конечный datetime (UTC).

        Returns:
            Список строк результата запроса.
        """
        return await execute_usage_timeline_query(
            self.session,
            user_id=str(self.user_id),
            start_ts=start_dt,
            end_ts=end_dt,
            granularity=self.granularity,
            top_domains_limit=self.top_domains_limit,
        )

    @staticmethod
    def _build_data(rows: list[UsageTimelineRow]) -> list[AnalyticsTimelineDataPoint]:
        """Приватный метод преобразования строк запроса в data ответа.

        Args:
            rows: Результат SQL-запроса timeline.

        Returns:
            Список AnalyticsTimelineDataPoint для поля data ответа.
        """
        return [
            AnalyticsTimelineDataPoint(
                bucket_start=row["bucket_start"],
                total_seconds=int(row.get("total_seconds", 0) or 0),
                unique_domains=int(row.get("unique_domains", 0) or 0),
                domains=ComputeUsageTimelineService._parse_domains(row.get("domains")),
            )
            for row in rows
        ]

    async def exec(self) -> AnalyticsTimelineResponseOkSchema | NoReturn:
        """Метод вычисления timeline статистики активности пользователя.

        Процесс включает:
        1. Построение временного диапазона по датам (UTC)
        2. Выполнение SQL-запроса агрегации по бакетам времени
        3. Сборку ответа (бакеты + топ доменов по каждому бакету)

        Returns:
            AnalyticsTimelineResponseOkSchema с агрегированной статистикой по временным бакетам.

        Raises:
            ServiceDatabaseErrorException: При ошибке запроса к базе данных.
            AnalyticsServiceException: При любой другой непредвиденной ошибке.
        """
        try:
            start_dt, end_dt = self._build_time_range(self.start_date, self.end_date)
            rows = await self._fetch_timeline(start_dt=start_dt, end_dt=end_dt)
            data = self._build_data(rows)

            logger.info(f"Successfully computed timeline analytics for user {self.user_id}")

            return AnalyticsTimelineResponseOkSchema(
                code="OK",
                message="analytics.messages.timeline_computed",
                from_date=self.start_date,
                to_date=self.end_date,
                granularity=self.granularity,
                data=data,
            )
        except SQLAlchemyError as exc:
            logger.exception(f"Failed to compute timeline analytics due to database error for user {self.user_id}")
            raise ServiceDatabaseErrorException(
                key="analytics.errors.database_query_error",
                fallback="Failed to query database for usage timeline analytics",
            ) from exc
        except Exception:
            raise AnalyticsServiceException(
                key="analytics.errors.unexpected_error",
                fallback="An unexpected error occurred while processing analytics timeline",
            )
