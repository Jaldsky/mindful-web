import asyncio
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from . import common
from .types import DomainUsageRow, UsageSummaryRow, UsageTimelineRow


async def execute_domain_usage_query(
    session: Session | AsyncSession,
    *,
    user_id: str,
    start_ts: datetime,
    end_ts: datetime,
    offset: int,
    limit: int,
    sort_by: str = "total_seconds",
    order: str = "desc",
    search: str | None = None,
) -> list[DomainUsageRow]:
    """Функция выполнения SQL-запроса вычисления статистики использования доменов.

    Args:
        session: Sync или Async сессия SQLAlchemy.
        user_id: Идентификатор пользователя.
        start_ts: Начало интервала.
        end_ts: Конец интервала.
        offset: Смещение для пагинации.
        limit: Лимит для пагинации.

    Returns:
        Список строк запроса в виде словарей.
    """
    stmt = text(common.load_sql("compute_domain_usage.sql"))
    params = {
        "user_id": user_id,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "offset": offset,
        "limit": limit,
        "sort_by": sort_by,
        "sort_order": order,
        "search": search,
    }

    if isinstance(session, AsyncSession):
        result = await session.execute(stmt, params)
    else:
        result = await asyncio.to_thread(session.execute, stmt, params)

    return list(result.mappings().all())


async def execute_usage_summary_query(
    session: Session | AsyncSession,
    *,
    user_id: str,
    start_ts: datetime,
    end_ts: datetime,
) -> UsageSummaryRow:
    """Функция выполнения SQL-запроса вычисления summary статистики использования.

    Args:
        session: Sync или Async сессия SQLAlchemy.
        user_id: Идентификатор пользователя.
        start_ts: Начало интервала.
        end_ts: Конец интервала.

    Returns:
        Словарь со сводными метриками.
    """
    stmt = text(common.load_sql("compute_usage_summary.sql"))
    params = {
        "user_id": user_id,
        "start_ts": start_ts,
        "end_ts": end_ts,
    }

    if isinstance(session, AsyncSession):
        result = await session.execute(stmt, params)
    else:
        result = await asyncio.to_thread(session.execute, stmt, params)

    row = result.mappings().first()
    if row is None:
        return {
            "total_seconds": 0,
            "total_domains": 0,
            "avg_seconds_per_domain": 0,
            "top_domain": None,
            "top_domain_seconds": 0,
        }
    return dict(row)


async def execute_usage_timeline_query(
    session: Session | AsyncSession,
    *,
    user_id: str,
    start_ts: datetime,
    end_ts: datetime,
    granularity: str = "day",
    top_domains_limit: int = 5,
) -> list[UsageTimelineRow]:
    """Функция выполнения SQL-запроса вычисления timeline статистики использования.

    Args:
        session: Sync или Async сессия SQLAlchemy.
        user_id: Идентификатор пользователя.
        start_ts: Начало интервала.
        end_ts: Конец интервала.
        granularity: Гранулярность агрегации (day или hour).
        top_domains_limit: Максимум доменов в каждом временном бакете.

    Returns:
        Список временных бакетов со статистикой.
    """
    stmt = text(common.load_sql("compute_timeline_usage.sql"))
    params = {
        "user_id": user_id,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "granularity": granularity,
        "top_domains_limit": top_domains_limit,
    }

    if isinstance(session, AsyncSession):
        result = await session.execute(stmt, params)
    else:
        result = await asyncio.to_thread(session.execute, stmt, params)

    return list(result.mappings().all())
