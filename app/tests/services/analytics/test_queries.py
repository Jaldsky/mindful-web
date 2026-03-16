import asyncio
from datetime import datetime, timezone
from unittest import IsolatedAsyncioTestCase
from unittest.mock import ANY, AsyncMock, Mock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics.queries import (
    execute_domain_usage_query,
    execute_usage_summary_query,
    execute_usage_timeline_query,
)


class TestAnalyticsQueries(IsolatedAsyncioTestCase):
    """Тесты функций queries.py (SQL-выполнение для analytics)."""

    async def test_execute_domain_usage_query_async_session(self):
        """Ветка AsyncSession: запрос выполняется через session.execute."""
        session = AsyncMock()
        start_ts = datetime(2025, 4, 5, 0, 0, tzinfo=timezone.utc)
        end_ts = datetime(2025, 4, 5, 23, 59, tzinfo=timezone.utc)
        expected_rows = [
            {"domain": "docs.google.com", "category": "work", "total_seconds": 2100, "total_items": 1},
        ]
        result_obj = Mock()
        result_obj.mappings.return_value.all.return_value = expected_rows
        session.execute.return_value = result_obj

        with (
            patch("app.services.analytics.queries.common.load_sql", return_value="SELECT 1") as mock_load_sql,
            patch(
                "app.services.analytics.queries.isinstance",
                side_effect=lambda obj, cls: obj is session and cls == AsyncSession,
            ),
        ):
            rows = await execute_domain_usage_query(
                session,
                user_id="u-1",
                start_ts=start_ts,
                end_ts=end_ts,
                offset=0,
                limit=50,
            )

        self.assertEqual(rows, expected_rows)
        mock_load_sql.assert_called_once_with("compute_domain_usage.sql")
        session.execute.assert_called_once()
        _, call_args, call_kwargs = session.execute.mock_calls[0]
        self.assertEqual(call_kwargs, {})
        params = call_args[1]
        self.assertEqual(
            params,
            {
                "user_id": "u-1",
                "start_ts": start_ts,
                "end_ts": end_ts,
                "offset": 0,
                "limit": 50,
                "sort_by": "total_seconds",
                "sort_order": "desc",
                "search": None,
            },
        )

    async def test_execute_domain_usage_query_sync_session_uses_to_thread(self):
        """Ветка sync Session: запрос выполняется через asyncio.to_thread."""
        session = Mock()
        start_ts = datetime(2025, 4, 5, 0, 0, tzinfo=timezone.utc)
        end_ts = datetime(2025, 4, 5, 23, 59, tzinfo=timezone.utc)
        expected_rows = [{"domain": "youtube.com", "category": "entertainment", "total_seconds": 600}]
        result_obj = Mock()
        result_obj.mappings.return_value.all.return_value = expected_rows

        with (
            patch("app.services.analytics.queries.common.load_sql", return_value="SELECT 1") as mock_load_sql,
            patch("app.services.analytics.queries.asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
            patch("app.services.analytics.queries.isinstance", return_value=False),
        ):
            mock_to_thread.return_value = result_obj
            rows = await execute_domain_usage_query(
                session,
                user_id="u-2",
                start_ts=start_ts,
                end_ts=end_ts,
                offset=10,
                limit=20,
            )

        self.assertEqual(rows, expected_rows)
        mock_load_sql.assert_called_once_with("compute_domain_usage.sql")
        mock_to_thread.assert_awaited_once()
        _, to_thread_args, to_thread_kwargs = mock_to_thread.mock_calls[0]
        self.assertEqual(to_thread_args[0], session.execute)
        self.assertEqual(to_thread_args[1], ANY)
        self.assertEqual(
            to_thread_args[2],
            {
                "user_id": "u-2",
                "start_ts": start_ts,
                "end_ts": end_ts,
                "offset": 10,
                "limit": 20,
                "sort_by": "total_seconds",
                "sort_order": "desc",
                "search": None,
            },
        )

    async def test_execute_usage_summary_query_async_session(self):
        """Ветка AsyncSession: summary-запрос возвращает словарь метрик."""
        session = AsyncMock()
        start_ts = datetime(2025, 4, 5, 0, 0, tzinfo=timezone.utc)
        end_ts = datetime(2025, 4, 5, 23, 59, tzinfo=timezone.utc)
        expected_row = {
            "total_seconds": 322,
            "total_domains": 1,
            "avg_seconds_per_domain": 322,
            "top_domain": "reddit.com",
            "top_domain_seconds": 322,
        }
        result_obj = Mock()
        result_obj.mappings.return_value.first.return_value = expected_row
        session.execute.return_value = result_obj

        with (
            patch("app.services.analytics.queries.common.load_sql", return_value="SELECT 1") as mock_load_sql,
            patch(
                "app.services.analytics.queries.isinstance",
                side_effect=lambda obj, cls: obj is session and cls == AsyncSession,
            ),
        ):
            row = await execute_usage_summary_query(
                session,
                user_id="u-3",
                start_ts=start_ts,
                end_ts=end_ts,
            )

        self.assertEqual(row, expected_row)
        mock_load_sql.assert_called_once_with("compute_usage_summary.sql")
        session.execute.assert_called_once()

    async def test_execute_usage_summary_query_returns_fallback_for_empty_result(self):
        """При пустом результате summary возвращается дефолтный payload с нулями."""
        session = AsyncMock()
        start_ts = datetime(2025, 4, 5, 0, 0, tzinfo=timezone.utc)
        end_ts = datetime(2025, 4, 5, 23, 59, tzinfo=timezone.utc)
        result_obj = Mock()
        result_obj.mappings.return_value.first.return_value = None
        session.execute.return_value = result_obj

        with (
            patch("app.services.analytics.queries.common.load_sql", return_value="SELECT 1"),
            patch(
                "app.services.analytics.queries.isinstance",
                side_effect=lambda obj, cls: obj is session and cls == AsyncSession,
            ),
        ):
            row = await execute_usage_summary_query(
                session,
                user_id="u-4",
                start_ts=start_ts,
                end_ts=end_ts,
            )

        self.assertEqual(
            row,
            {
                "total_seconds": 0,
                "total_domains": 0,
                "avg_seconds_per_domain": 0,
                "top_domain": None,
                "top_domain_seconds": 0,
            },
        )

    async def test_execute_usage_summary_query_sync_session_uses_to_thread(self):
        """Ветка sync Session для summary: используется asyncio.to_thread."""
        session = Mock()
        start_ts = datetime(2025, 4, 5, 0, 0, tzinfo=timezone.utc)
        end_ts = datetime(2025, 4, 5, 23, 59, tzinfo=timezone.utc)
        expected_row = {
            "total_seconds": 100,
            "total_domains": 1,
            "avg_seconds_per_domain": 100,
            "top_domain": "example.com",
            "top_domain_seconds": 100,
        }
        result_obj = Mock()
        result_obj.mappings.return_value.first.return_value = expected_row

        with (
            patch("app.services.analytics.queries.common.load_sql", return_value="SELECT 1") as mock_load_sql,
            patch("app.services.analytics.queries.asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
            patch("app.services.analytics.queries.isinstance", return_value=False),
        ):
            mock_to_thread.return_value = result_obj
            row = await execute_usage_summary_query(
                session,
                user_id="u-5",
                start_ts=start_ts,
                end_ts=end_ts,
            )

        self.assertEqual(row, expected_row)
        mock_load_sql.assert_called_once_with("compute_usage_summary.sql")
        mock_to_thread.assert_awaited_once_with(
            session.execute,
            ANY,
            {
                "user_id": "u-5",
                "start_ts": start_ts,
                "end_ts": end_ts,
            },
        )

    async def test_execute_usage_timeline_query_async_session(self):
        """Ветка AsyncSession: timeline-запрос выполняется через session.execute."""
        session = AsyncMock()
        start_ts = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        end_ts = datetime(2025, 1, 2, 0, 0, tzinfo=timezone.utc)
        expected_rows = [
            {
                "bucket_start": datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc),
                "total_seconds": 3600,
                "unique_domains": 2,
                "domains": [{"domain": "example.com", "total_seconds": 1800}],
            }
        ]
        result_obj = Mock()
        result_obj.mappings.return_value.all.return_value = expected_rows
        session.execute.return_value = result_obj

        with (
            patch("app.services.analytics.queries.common.load_sql", return_value="SELECT 1") as mock_load_sql,
            patch(
                "app.services.analytics.queries.isinstance",
                side_effect=lambda obj, cls: obj is session and cls == AsyncSession,
            ),
        ):
            rows = await execute_usage_timeline_query(
                session,
                user_id="u-6",
                start_ts=start_ts,
                end_ts=end_ts,
                granularity="hour",
                top_domains_limit=7,
            )

        self.assertEqual(rows, expected_rows)
        mock_load_sql.assert_called_once_with("compute_timeline_usage.sql")
        session.execute.assert_called_once()
        _, call_args, call_kwargs = session.execute.mock_calls[0]
        self.assertEqual(call_kwargs, {})
        params = call_args[1]
        self.assertEqual(
            params,
            {
                "user_id": "u-6",
                "start_ts": start_ts,
                "end_ts": end_ts,
                "granularity": "hour",
                "top_domains_limit": 7,
            },
        )

    async def test_execute_usage_timeline_query_sync_session_uses_to_thread(self):
        """Ветка sync Session для timeline: используется asyncio.to_thread."""
        session = Mock()
        start_ts = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        end_ts = datetime(2025, 1, 1, 23, 59, tzinfo=timezone.utc)
        expected_rows = [{"bucket_start": start_ts, "total_seconds": 0, "unique_domains": 0, "domains": []}]
        result_obj = Mock()
        result_obj.mappings.return_value.all.return_value = expected_rows

        with (
            patch("app.services.analytics.queries.common.load_sql", return_value="SELECT 1") as mock_load_sql,
            patch("app.services.analytics.queries.asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
            patch("app.services.analytics.queries.isinstance", return_value=False),
        ):
            mock_to_thread.return_value = result_obj
            rows = await execute_usage_timeline_query(
                session,
                user_id="u-7",
                start_ts=start_ts,
                end_ts=end_ts,
                granularity="day",
                top_domains_limit=5,
            )

        self.assertEqual(rows, expected_rows)
        mock_load_sql.assert_called_once_with("compute_timeline_usage.sql")
        mock_to_thread.assert_awaited_once()
        _, to_thread_args, to_thread_kwargs = mock_to_thread.mock_calls[0]
        self.assertEqual(to_thread_args[0], session.execute)
        self.assertEqual(to_thread_args[1], ANY)
        self.assertEqual(
            to_thread_args[2],
            {
                "user_id": "u-7",
                "start_ts": start_ts,
                "end_ts": end_ts,
                "granularity": "day",
                "top_domains_limit": 5,
            },
        )
