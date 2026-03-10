import asyncio
from uuid import UUID
from celery import shared_task

from ..analytics.types import Date, Page
from ...config import DEFAULT_PAGE_SIZE
from ...db.session.provider import Provider
from ..analytics import ComputeDomainUsageService, ComputeUsageSummaryService


@shared_task(name="analytics.compute_domain_usage")
def compute_domain_usage_task(
    user_id: UUID,
    start_date: Date,
    end_date: Date,
    page: Page = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict:
    """Celery задача вычисления статистики использования по доменам.

    Args:
        user_id: Идентификатор пользователя.
        start_date: Начало временного диапазона.
        end_date: Конец временного диапазона.
        page: Номер страницы.
        page_size: Размер страницы.

    Returns:
        Словарь с результатами аналитики.
    """
    provider = Provider()
    with provider.sync_manager.get_session() as session:
        service = ComputeDomainUsageService(
            session=session,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )
        result_schema = asyncio.run(service.exec())
        return result_schema.model_dump(mode="json")


@shared_task(name="analytics.compute_usage_summary")
def compute_usage_summary_task(
    user_id: UUID,
    start_date: Date,
    end_date: Date,
) -> dict:
    """Celery задача вычисления summary статистики использования.

    Args:
        user_id: Идентификатор пользователя.
        start_date: Начало временного диапазона.
        end_date: Конец временного диапазона.

    Returns:
        Словарь со сводными результатами аналитики.
    """
    provider = Provider()
    with provider.sync_manager.get_session() as session:
        service = ComputeUsageSummaryService(
            session=session,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        result_schema = asyncio.run(service.exec())
        return result_schema.model_dump(mode="json")
