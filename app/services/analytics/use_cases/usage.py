from typing import Any
from uuid import UUID

from ..types import Page, Date, PageSize, SortBy, SortOrder
from ....schemas.analytics import AnalyticsDomainsResponseOkSchema
from ....config import DEFAULT_PAGE_SIZE


class AnalyticsDomainsService:
    """Сервис получения статистики активности пользователя по доменам."""

    async def exec(
        self,
        user_id: UUID,
        from_date: Date,
        to_date: Date,
        page: Page = 1,
        per_page: PageSize = DEFAULT_PAGE_SIZE,
        sort_by: SortBy = "total_seconds",
        order: SortOrder = "desc",
        search: str | None = None,
    ) -> AnalyticsDomainsResponseOkSchema:
        """Метод получения статистики использования по доменам.

        Процесс включает:
        1. Постановку задачи вычисления в очередь
        2. Ожидание результата в рамках таймаута orchestrator
        3. Приведение результата к схеме ответа

        Args:
            user_id: Идентификатор пользователя.
            from_date: Начало периода.
            to_date: Конец периода.
            page: Номер страницы.
            per_page: Размер страницы (количество доменов на странице).
            sort_by: Поле сортировки агрегатов по доменам.
            order: Направление сортировки (asc или desc).
            search: Поисковая строка для фильтрации доменов по подстроке.

        Returns:
            Схема ответа AnalyticsDomainsResponseOkSchema.

        Raises:
            OrchestratorTimeoutException: Если задача не успела выполниться в пределах таймаута (202).
            OrchestratorBrokerUnavailableException: Если брокер Celery недоступен (503).
        """
        from ...scheduler import Orchestrator, compute_domain_usage_task

        orchestrator = Orchestrator()
        data_dict: dict[str, Any] = orchestrator.exec(
            task=compute_domain_usage_task,
            user_id=user_id,
            start_date=from_date,
            end_date=to_date,
            page=page,
            page_size=per_page,
            sort_by=sort_by,
            order=order,
            search=search,
        )
        return AnalyticsDomainsResponseOkSchema(**data_dict)
