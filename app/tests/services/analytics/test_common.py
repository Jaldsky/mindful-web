from unittest import TestCase
from unittest.mock import patch

from app.services.analytics.common import load_sql


class TestAnalyticsCommon(TestCase):
    """Тесты для app.services.analytics.common."""

    @patch("app.services.analytics.common.read_text_file")
    def test_load_sql_reads_file(self, mock_read_text_file):
        """SQL loader читает файл и возвращает его содержимое."""
        mock_read_text_file.return_value = "SELECT 1"

        sql = load_sql("compute_domain_usage.sql")
        self.assertEqual(sql, "SELECT 1")

        sql = load_sql("compute_usage_summary.sql")
        self.assertEqual(sql, "SELECT 1")

        self.assertEqual(mock_read_text_file.call_count, 2)

    @patch("app.services.analytics.common.read_text_file")
    def test_load_sql_calls_reader_with_utf8_encoding(self, mock_read_text_file):
        """SQL loader передает путь и utf-8 в read_text_file."""
        mock_read_text_file.return_value = "SELECT 42"

        load_sql("compute_domain_usage.sql")

        mock_read_text_file.assert_called_once()
        call_args, call_kwargs = mock_read_text_file.call_args
        self.assertEqual(call_kwargs.get("encoding"), "utf-8")
        self.assertTrue(str(call_args[0]).endswith("sql/compute_domain_usage.sql"))

    @patch("app.services.analytics.common.read_text_file")
    def test_load_sql_builds_expected_path_for_summary(self, mock_read_text_file):
        """SQL loader строит корректный путь для summary SQL."""
        mock_read_text_file.return_value = "SELECT 7"

        load_sql("compute_usage_summary.sql")

        call_args, call_kwargs = mock_read_text_file.call_args
        self.assertEqual(call_kwargs.get("encoding"), "utf-8")
        self.assertTrue(str(call_args[0]).endswith("sql/compute_usage_summary.sql"))
