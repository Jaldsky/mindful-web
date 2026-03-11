import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Any, NoReturn
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ...exceptions import ServiceDatabaseErrorException
from ....config import DEFAULT_PAGE_SIZE
from ....schemas.analytics.usage.response_ok_schema import (
    AnalyticsDomainsResponseOkSchema,
    DomainUsageData,
    PaginationMeta,
)
from ..types import Date, Page, PageSize, DomainUsageRow, SortBy, SortOrder
from ..exceptions import AnalyticsServiceException
from ..queries import execute_domain_usage_query

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class ComputeDomainUsageData:
    """Входные данные для вычисления статистики использования доменов."""

    user_id: UUID
    start_date: Date
    end_date: Date
    page: Page = 1
    page_size: PageSize = DEFAULT_PAGE_SIZE
    sort_by: SortBy = "total_seconds"
    order: SortOrder = "desc"
    search: str | None = None


class ComputeDomainUsageServiceBase:
    """Базовый класс сервиса вычисления статистики доменов."""

    session: Session | AsyncSession
    _data: ComputeDomainUsageData

    def __init__(self, session: Session | AsyncSession, **kwargs: Any) -> None:
        """Инициализация сервиса вычисления статистики доменов.

        Args:
            session: Sync или Async сессия SQLAlchemy.
            **kwargs: Аргументы для ComputeDomainUsageData.
        """
        self.session = session
        self._data = ComputeDomainUsageData(**kwargs)

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
    def page(self) -> Page:
        """Свойство получения номера страницы.

        Returns:
            Номер страницы.
        """
        return self._data.page

    @property
    def page_size(self) -> PageSize:
        """Свойство получения размера страницы.

        Returns:
            Размер страницы.
        """
        return self._data.page_size

    @property
    def sort_by(self) -> SortBy:
        """Свойство получения поля сортировки.

        Returns:
            Поле сортировки.
        """
        return self._data.sort_by

    @property
    def order(self) -> SortOrder:
        """Свойство получения направления сортировки.

        Returns:
            Направление сортировки.
        """
        return self._data.order

    @property
    def search(self) -> str | None:
        """Свойство получения поисковой строки по домену.

        Returns:
            Поисковая строка по домену или None.
        """
        return self._data.search


class ComputeDomainUsageService(ComputeDomainUsageServiceBase):
    """Сервис вычисления статистики активности пользователя по доменам."""

    @staticmethod
    def _normalize_pagination(page: Page, page_size: PageSize) -> tuple[Page, PageSize]:
        """Приватный метод нормализации параметров пагинации.

        Args:
            page: Номер страницы.
            page_size: Размер страницы.

        Returns:
            Кортеж (page, page_size) с нормализованными значениями.
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = DEFAULT_PAGE_SIZE
        return page, page_size

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

    async def _fetch_rows(
        self,
        *,
        start_dt: datetime,
        end_dt: datetime,
        page: Page,
        page_size: PageSize,
    ) -> list[DomainUsageRow]:
        """Приватный метод выполнения SQL-запроса по подсчету количества времени на домен.

        Args:
            start_dt: Начальный datetime (UTC).
            end_dt: Конечный datetime (UTC).
            page: Номер страницы.
            page_size: Размер страницы.

        Returns:
            Список строк запроса в виде словарей.
        """
        return await execute_domain_usage_query(
            self.session,
            user_id=str(self.user_id),
            start_ts=start_dt,
            end_ts=end_dt,
            offset=(page - 1) * page_size,
            limit=page_size,
            sort_by=self.sort_by,
            order=self.order,
            search=self.search,
        )

    @staticmethod
    def _build_pagination(rows: list[DomainUsageRow], page: Page, page_size: PageSize) -> PaginationMeta:
        """Приватный метод построения метаданных пагинации.

        Args:
            rows: Результат SQL запроса.
            page: Текущая страница.
            page_size: Размер страницы.

        Returns:
            Объект PaginationMeta.
        """
        total_items = rows[0]["total_items"] if rows else 0
        return PaginationMeta(
            page=page,
            per_page=page_size,
            total_items=int(total_items),
            total_pages=(total_items + page_size - 1) // page_size if page_size > 0 else 0,
            next=None,
            prev=None,
        )

    @staticmethod
    def _build_data(rows: list[DomainUsageRow]) -> list[DomainUsageData]:
        """Приватный метод преобразования строк запроса в data[] ответа.

        Args:
            rows: Результат SQL запроса.

        Returns:
            Список DomainUsageData для поля data ответа.
        """
        return [
            DomainUsageData(domain=r["domain"], category=r["category"], total_seconds=int(r["total_seconds"]))
            for r in rows
        ]

    async def exec(self) -> AnalyticsDomainsResponseOkSchema | NoReturn:
        """Метод вычисления статистики активности пользователя по доменам.

        Процесс включает:
        1. Нормализацию параметров пагинации
        2. Построение временного диапазона (UTC) по датам
        3. Выполнение SQL запроса агрегации по доменам
        4. Сборку схемы ответа с пагинацией и данными

        Returns:
            AnalyticsDomainsResponseOkSchema с агрегированной статистикой.

        Raises:
            ServiceDatabaseErrorException: При ошибке запроса к базе данных.
            AnalyticsServiceException: При любой другой непредвиденной ошибке.
        """
        try:
            page, page_size = self._normalize_pagination(self.page, self.page_size)
            start_dt, end_dt = self._build_time_range(self.start_date, self.end_date)

            rows = await self._fetch_rows(start_dt=start_dt, end_dt=end_dt, page=page, page_size=page_size)
            pagination_meta = self._build_pagination(rows, page, page_size)
            data = self._build_data(rows)

            logger.info(f"Successfully computed domains analytics for user {self.user_id}")

            return AnalyticsDomainsResponseOkSchema(
                code="OK",
                message="analytics.messages.usage_computed",
                from_date=self.start_date,
                to_date=self.end_date,
                pagination=pagination_meta,
                data=data,
            )
        except SQLAlchemyError:
            raise ServiceDatabaseErrorException(
                key="analytics.errors.database_query_error",
                fallback="Failed to query database for usage analytics",
            )
        except Exception:
            raise AnalyticsServiceException(
                key="analytics.errors.unexpected_error",
                fallback="An unexpected error occurred while processing analytics",
            )
