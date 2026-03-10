import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Any, NoReturn
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ....schemas.analytics.summary.response_ok_schema import (
    AnalyticsSummaryData,
    AnalyticsSummaryResponseOkSchema,
)
from ....services.exceptions import ServiceDatabaseErrorException
from ..exceptions import AnalyticsServiceException
from ..queries import execute_usage_summary_query
from ..types import Date, UsageSummaryRow

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class ComputeUsageSummaryData:
    """Входные данные для вычисления summary статистики использования."""

    user_id: UUID
    start_date: Date
    end_date: Date


class ComputeUsageSummaryServiceBase:
    """Базовый класс сервиса вычисления summary статистики доменов."""

    session: Session | AsyncSession
    _data: ComputeUsageSummaryData

    def __init__(self, session: Session | AsyncSession, **kwargs: Any) -> None:
        """Инициализация сервиса вычисления summary статистики доменов.

        Args:
            session: Sync или Async сессия SQLAlchemy.
            **kwargs: Аргументы для ComputeUsageSummaryData.
        """
        self.session = session
        self._data = ComputeUsageSummaryData(**kwargs)

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


class ComputeUsageSummaryService(ComputeUsageSummaryServiceBase):
    """Сервис вычисления summary статистики активности пользователя по доменам."""

    @staticmethod
    def _build_time_range(start_date: Date, end_date: Date) -> tuple[datetime, datetime]:
        """Приватный метод построения временного диапазона (UTC) по датам.

        Args:
            start_date: Дата начала периода.
            end_date: Дата окончания периода.

        Returns:
            Кортеж (start_dt, end_dt) в UTC.
        """
        start_dt = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)
        return start_dt, end_dt

    async def _fetch_summary(self, *, start_dt: datetime, end_dt: datetime) -> UsageSummaryRow:
        """Приватный метод выполнения SQL-запроса summary статистики.

        Args:
            start_dt: Начальный datetime (UTC).
            end_dt: Конечный datetime (UTC).

        Returns:
            Словарь со сводными метриками.
        """
        return await execute_usage_summary_query(
            self.session,
            user_id=str(self.user_id),
            start_ts=start_dt,
            end_ts=end_dt,
        )

    @staticmethod
    def _build_data(row: UsageSummaryRow) -> AnalyticsSummaryData:
        """Приватный метод преобразования row запроса в data ответа.

        Args:
            row: Результат SQL-запроса.

        Returns:
            Объект AnalyticsSummaryData.
        """
        return AnalyticsSummaryData(
            total_seconds=int(row.get("total_seconds", 0) or 0),
            total_domains=int(row.get("total_domains", 0) or 0),
            avg_seconds_per_domain=int(row.get("avg_seconds_per_domain", 0) or 0),
            top_domain=row.get("top_domain"),
            top_domain_seconds=int(row.get("top_domain_seconds", 0) or 0),
        )

    async def exec(self) -> AnalyticsSummaryResponseOkSchema | NoReturn:
        """Метод вычисления summary статистики активности пользователя по доменам.

        Процесс включает:
        1. Построение временного диапазона (UTC) по датам
        2. Выполнение SQL-запроса summary агрегации
        3. Сборку схемы ответа с итоговыми метриками

        Returns:
            AnalyticsSummaryResponseOkSchema со сводной статистикой.

        Raises:
            ServiceDatabaseErrorException: При ошибке запроса к базе данных.
            AnalyticsServiceException: При любой другой непредвиденной ошибке.
        """
        try:
            start_dt, end_dt = self._build_time_range(self.start_date, self.end_date)
            row = await self._fetch_summary(start_dt=start_dt, end_dt=end_dt)
            data = self._build_data(row)

            logger.info(f"Successfully computed usage analytics summary for user {self.user_id}")

            return AnalyticsSummaryResponseOkSchema(
                code="OK",
                message="analytics.messages.summary_computed",
                from_date=self.start_date,
                to_date=self.end_date,
                data=data,
            )
        except SQLAlchemyError:
            raise ServiceDatabaseErrorException(
                key="analytics.errors.database_query_error",
                fallback="Failed to query database for usage summary analytics",
            )
        except Exception:
            raise AnalyticsServiceException(
                key="analytics.errors.unexpected_error",
                fallback="An unexpected error occurred while processing analytics summary",
            )
