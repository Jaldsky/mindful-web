from datetime import date
from typing import Any
from uuid import UUID

from ....schemas.analytics import AnalyticsSummaryResponseOkSchema


class AnalyticsSummaryService:
    """Сервис получения summary статистики активности пользователя."""

    async def exec(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
    ) -> AnalyticsSummaryResponseOkSchema:
        """Метод получения summary статистики использования по доменам.

        Args:
            user_id: Идентификатор пользователя.
            from_date: Начало периода.
            to_date: Конец периода.

        Returns:
            Схема ответа AnalyticsSummaryResponseOkSchema.

        Raises:
            OrchestratorTimeoutException: Если задача не успела выполниться в пределах таймаута (202).
            OrchestratorBrokerUnavailableException: Если брокер Celery недоступен (503).
        """
        from ...scheduler import Orchestrator, compute_usage_summary_task

        orchestrator = Orchestrator()
        data_dict: dict[str, Any] = orchestrator.exec(
            task=compute_usage_summary_task,
            user_id=user_id,
            start_date=from_date,
            end_date=to_date,
        )
        return AnalyticsSummaryResponseOkSchema(**data_dict)
