from datetime import date
from typing import Any
from uuid import UUID

from ....schemas.analytics import AnalyticsTimelineResponseOkSchema
from ..types import TimelineGranularity, TopDomainsLimit


class AnalyticsTimelineService:
    """Сервис получения timeline статистики активности пользователя."""

    async def exec(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
        granularity: TimelineGranularity = "day",
        top_domains_limit: TopDomainsLimit = 5,
    ) -> AnalyticsTimelineResponseOkSchema:
        """Метод получения timeline статистики использования.

        Args:
            user_id: Идентификатор пользователя.
            from_date: Начало периода.
            to_date: Конец периода.
            granularity: Гранулярность агрегации.
            top_domains_limit: Максимум доменов в каждом бакете.

        Returns:
            Схема ответа AnalyticsTimelineResponseOkSchema.

        Raises:
            OrchestratorTimeoutException: Если задача не успела выполниться в пределах таймаута (202).
            OrchestratorBrokerUnavailableException: Если брокер Celery недоступен (503).
        """
        from ...scheduler import Orchestrator, compute_usage_timeline_task

        orchestrator = Orchestrator()
        data_dict: dict[str, Any] = orchestrator.exec(
            task=compute_usage_timeline_task,
            user_id=user_id,
            start_date=from_date,
            end_date=to_date,
            granularity=granularity,
            top_domains_limit=top_domains_limit,
        )
        return AnalyticsTimelineResponseOkSchema(**data_dict)
