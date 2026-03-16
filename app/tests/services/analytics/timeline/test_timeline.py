import asyncio
from datetime import datetime, timezone, date
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics import ComputeUsageTimelineService
from app.schemas.analytics.timeline.response_ok_schema import AnalyticsTimelineResponseOkSchema


class TestTimelineService(TestCase):
    """Тесты для ComputeUsageTimelineService."""

    def setUp(self):
        self.session = AsyncMock()
        self.user_id = uuid4()
        self.start_date = date(2025, 4, 5)
        self.end_date = date(2025, 4, 5)

    def _run_async(self, coro):
        """Вспомогательный метод для запуска асинхронного кода."""
        return asyncio.run(coro)

    def test_parse_domains_accepts_list(self):
        """_parse_domains принимает список словарей (json/jsonb) и нормализует значения."""
        raw = [
            {"domain": "youtube.com", "total_seconds": 600},
            {"domain": "docs.google.com", "total_seconds": "1200"},
        ]
        parsed = ComputeUsageTimelineService._parse_domains(raw)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0].domain, "youtube.com")
        self.assertEqual(parsed[0].total_seconds, 600)
        self.assertEqual(parsed[1].domain, "docs.google.com")
        self.assertEqual(parsed[1].total_seconds, 1200)

    def test_parse_domains_accepts_json_string(self):
        """_parse_domains принимает JSON-строку и парсит её в список доменов."""
        raw = '[{"domain":"github.com","total_seconds":900}]'
        parsed = ComputeUsageTimelineService._parse_domains(raw)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].domain, "github.com")
        self.assertEqual(parsed[0].total_seconds, 900)

    def test_parse_domains_invalid_returns_empty(self):
        """_parse_domains возвращает [] для мусорных значений."""
        self.assertEqual(ComputeUsageTimelineService._parse_domains(None), [])
        self.assertEqual(ComputeUsageTimelineService._parse_domains({}), [])
        self.assertEqual(ComputeUsageTimelineService._parse_domains("not-json"), [])
        self.assertEqual(ComputeUsageTimelineService._parse_domains([{"total_seconds": 10}]), [])

    def test_build_data_sets_domains(self):
        """_build_data наполняет поле domains в каждом бакете."""
        rows = [
            {
                "bucket_start": datetime(2025, 4, 5, 10, 0, tzinfo=timezone.utc),
                "total_seconds": 1800,
                "unique_domains": 2,
                "domains": [
                    {"domain": "docs.google.com", "total_seconds": 1200},
                    {"domain": "youtube.com", "total_seconds": 600},
                ],
            }
        ]
        data = ComputeUsageTimelineService._build_data(rows)
        self.assertEqual(len(data), 1)
        self.assertEqual(len(data[0].domains), 2)
        self.assertEqual(data[0].domains[0].domain, "docs.google.com")

    @patch("app.services.analytics.jobs.compute_usage_timeline.logger")
    @patch("app.services.analytics.common.load_sql")
    @patch("app.services.analytics.queries.isinstance")
    def test_exec_success_parses_domains(self, mock_isinstance, mock_load_sql, _mock_logger):
        """exec возвращает схему и парсит domains из строки/объекта."""
        mock_isinstance.side_effect = lambda obj, cls: cls == AsyncSession
        mock_load_sql.return_value = "SELECT bucket_start, total_seconds, unique_domains, domains FROM x"
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {
                "bucket_start": datetime(2025, 4, 5, 0, 0, tzinfo=timezone.utc),
                "total_seconds": 2700,
                "unique_domains": 2,
                "domains": '[{"domain":"docs.google.com","total_seconds":2100},{"domain":"youtube.com","total_seconds":600}]',
            }
        ]
        self.session.execute = AsyncMock(return_value=mock_result)

        result = self._run_async(
            ComputeUsageTimelineService(
                session=self.session,
                user_id=self.user_id,
                start_date=self.start_date,
                end_date=self.end_date,
                granularity="day",
                top_domains_limit=5,
            ).exec()
        )

        self.assertIsInstance(result, AnalyticsTimelineResponseOkSchema)
        self.assertEqual(len(result.data), 1)
        self.assertEqual(len(result.data[0].domains), 2)
