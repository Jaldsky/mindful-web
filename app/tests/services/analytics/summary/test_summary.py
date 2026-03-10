import asyncio
from datetime import date, datetime, time, timezone
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID, uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.analytics.summary.response_ok_schema import AnalyticsSummaryResponseOkSchema
from app.services.analytics import ComputeUsageSummaryService
from app.services.analytics.exceptions import AnalyticsServiceException
from app.services.exceptions import ServiceDatabaseErrorException


class TestSummaryService(TestCase):
    """Тесты для ComputeUsageSummaryService."""

    def setUp(self):
        self.logger = Mock()
        self.session = AsyncMock()
        self.user_id: UUID = uuid4()
        self.start_date = date(2025, 4, 5)
        self.end_date = date(2025, 4, 6)

    def _run_async(self, coro):
        """Вспомогательный метод для запуска асинхронного кода."""
        return asyncio.run(coro)

    @patch("app.services.analytics.jobs.compute_usage_summary.logger")
    @patch("app.services.analytics.common.load_sql")
    @patch("app.services.analytics.queries.isinstance")
    def test_exec_success(self, mock_isinstance, mock_load_sql, mock_logger):
        """Успешное выполнение запроса summary аналитики на моках."""
        mock_isinstance.side_effect = lambda obj, cls: cls == AsyncSession
        mock_load_sql.return_value = "SELECT total_seconds, total_domains FROM summary"
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "total_seconds": 2700,
            "total_domains": 2,
            "avg_seconds_per_domain": 1350,
            "top_domain": "docs.google.com",
            "top_domain_seconds": 2100,
        }
        self.session.execute = AsyncMock(return_value=mock_result)

        result = self._run_async(
            ComputeUsageSummaryService(
                session=self.session,
                user_id=self.user_id,
                start_date=self.start_date,
                end_date=self.end_date,
            ).exec()
        )

        self.assertIsInstance(result, AnalyticsSummaryResponseOkSchema)
        self.assertEqual(result.code, "OK")
        self.assertEqual(result.from_date, self.start_date)
        self.assertEqual(result.to_date, self.end_date)
        self.assertEqual(result.data.total_seconds, 2700)
        self.assertEqual(result.data.total_domains, 2)
        self.assertEqual(result.data.top_domain, "docs.google.com")
        mock_logger.info.assert_called_with(f"Successfully computed usage analytics summary for user {self.user_id}")

    @patch("app.services.analytics.common.load_sql")
    @patch("app.services.analytics.queries.isinstance")
    def test_exec_database_query_fails(self, mock_isinstance, mock_load_sql):
        """Ошибка при запросе к базе данных."""
        mock_isinstance.side_effect = lambda obj, cls: cls == AsyncSession
        mock_load_sql.return_value = "SELECT * FROM test"
        self.session.execute = AsyncMock(side_effect=SQLAlchemyError("Connection lost"))

        with self.assertRaises(ServiceDatabaseErrorException) as cm:
            self._run_async(
                ComputeUsageSummaryService(
                    session=self.session,
                    user_id=self.user_id,
                    start_date=self.start_date,
                    end_date=self.end_date,
                ).exec()
            )

        self.assertEqual("analytics.errors.database_query_error", cm.exception.key)

    @patch("app.services.analytics.common.load_sql")
    @patch("app.services.analytics.queries.isinstance")
    def test_exec_unexpected_error(self, mock_isinstance, mock_load_sql):
        """Обработка неожиданного исключения."""
        mock_isinstance.side_effect = lambda obj, cls: cls == AsyncSession
        mock_load_sql.return_value = "SELECT * FROM test"
        self.session.execute = AsyncMock(side_effect=ValueError("Something weird"))

        with self.assertRaises(AnalyticsServiceException) as cm:
            self._run_async(
                ComputeUsageSummaryService(
                    session=self.session,
                    user_id=self.user_id,
                    start_date=self.start_date,
                    end_date=self.end_date,
                ).exec()
            )

        self.assertEqual("analytics.errors.unexpected_error", cm.exception.key)

    def test_build_time_range(self):
        """Метод _build_time_range корректно строит временной диапазон."""
        service = ComputeUsageSummaryService(
            session=self.session,
            user_id=self.user_id,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        start_dt, end_dt = service._build_time_range(self.start_date, self.end_date)

        self.assertIsInstance(start_dt, datetime)
        self.assertIsInstance(end_dt, datetime)
        self.assertEqual(start_dt.date(), self.start_date)
        self.assertEqual(end_dt.date(), self.end_date)
        self.assertEqual(start_dt.time(), time.min)
        self.assertEqual(end_dt.time(), time.max)
        self.assertEqual(start_dt.tzinfo, timezone.utc)
        self.assertEqual(end_dt.tzinfo, timezone.utc)

    @patch("app.services.analytics.common.load_sql")
    @patch("app.services.analytics.queries.isinstance")
    def test_exec_empty_result_returns_zeroed_summary(self, mock_isinstance, mock_load_sql):
        """Пустой результат запроса возвращает нулевые summary-метрики."""
        mock_isinstance.side_effect = lambda obj, cls: cls == AsyncSession
        mock_load_sql.return_value = "SELECT total_seconds, total_domains FROM summary"
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        self.session.execute = AsyncMock(return_value=mock_result)

        result = self._run_async(
            ComputeUsageSummaryService(
                session=self.session,
                user_id=self.user_id,
                start_date=self.start_date,
                end_date=self.end_date,
            ).exec()
        )

        self.assertEqual(result.data.total_seconds, 0)
        self.assertEqual(result.data.total_domains, 0)
        self.assertEqual(result.data.avg_seconds_per_domain, 0)
        self.assertIsNone(result.data.top_domain)
        self.assertEqual(result.data.top_domain_seconds, 0)
