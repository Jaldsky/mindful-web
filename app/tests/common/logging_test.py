import logging
import sys
from io import StringIO
from unittest import TestCase, mock
from unittest.mock import patch, MagicMock

from app.common.logging import setup_logging


class TestLogging(TestCase):
    def setUp(self):
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.NOTSET)

    def tearDown(self):
        logging.getLogger().handlers.clear()

    @patch("app.common.logging.logging.getLogger")
    @patch("app.common.logging.logging.basicConfig")
    def test_setup_logging_default_params(self, mock_basic_config: MagicMock, mock_get_logger: MagicMock):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = setup_logging()

        mock_basic_config.assert_called_once_with(
            level=logging.INFO,
            format="[%(levelname)s][%(name)s]:%(message)s",
            handlers=[mock.ANY],
        )
        mock_get_logger.assert_called_once_with("app.common.logging")
        self.assertEqual(logger, mock_logger)

    @patch("app.common.logging.logging.getLogger")
    @patch("app.common.logging.logging.basicConfig")
    def test_setup_logging_custom_params(self, mock_basic_config: MagicMock, mock_get_logger: MagicMock):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        custom_format = "[CUSTOM] %(message)s"

        logger = setup_logging(level=logging.DEBUG, forma=custom_format, force=True)

        mock_basic_config.assert_called_once_with(
            level=logging.DEBUG,
            format=custom_format,
            handlers=[mock.ANY],
            force=True,
        )
        mock_get_logger.assert_called_once_with("app.common.logging")
        self.assertEqual(logger, mock_logger)

    def test_logging_format_applied_correctly(self):
        """Интеграционный тест: проверяем, что сообщения логируются в нужном формате."""
        log_buffer = StringIO()
        with patch.object(sys, "stdout", log_buffer):
            logger = setup_logging()

            test_message = "Test log message"
            logger.info(test_message)

        log_output = log_buffer.getvalue().strip()

        expected = f"[INFO][app.common.logging]:{test_message}"
        self.assertEqual(log_output, expected)

    def test_logging_respects_custom_format(self):
        """Проверяем кастомный формат."""
        log_buffer = StringIO()
        custom_format = "[LOG] %(levelname)s - %(message)s"

        with patch.object(sys, "stdout", log_buffer):
            logger = setup_logging(forma=custom_format)
            logger.warning("Custom format test")

        log_output = log_buffer.getvalue().strip()
        expected = "[LOG] WARNING - Custom format test"
        self.assertEqual(log_output, expected)

    def test_setup_logging_is_idempotent_for_basic_config(self):
        """
        logging.basicConfig игнорируется после первого вызова,
        но наша функция всё равно должна возвращать логгер.
        """
        log_buffer = StringIO()
        with patch.object(sys, "stdout", log_buffer):
            logger1 = setup_logging()
            logger2 = setup_logging(level=logging.DEBUG)  # второй вызов

            logger1.info("First")
            logger2.error("Second")

        output = log_buffer.getvalue()
        # Оба сообщения должны быть в формате ПЕРВОГО вызова (INFO-level format)
        self.assertIn("[INFO][app.common.logging]:First", output)
        self.assertIn("[ERROR][app.common.logging]:Second", output)
        # Уровень логирования остаётся INFO (первый вызов), поэтому DEBUG не проходит — но это нормально

    def test_kwargs_passed_to_basic_config(self):
        """Проверяем, что **kwargs передаются в basicConfig."""
        with patch("app.common.logging.logging.basicConfig") as mock_basic_config:
            setup_logging(force=True, datefmt="%Y-%m-%d")
            mock_basic_config.assert_called_once_with(
                level=logging.INFO,
                format="[%(levelname)s][%(name)s]:%(message)s",
                handlers=[mock.ANY],
                force=True,
                datefmt="%Y-%m-%d",
            )
