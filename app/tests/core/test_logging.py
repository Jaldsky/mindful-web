import logging
from io import StringIO
from unittest import TestCase, mock
from unittest.mock import patch, MagicMock

from app.core.logging import setup_logging


class TestLogging(TestCase):
    def setUp(self):
        logging.disable(logging.NOTSET)
        setup_logging(force=True)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.WARNING)

        app_logger = logging.getLogger("app.core.logging")
        app_logger.setLevel(logging.NOTSET)
        app_logger.propagate = True

    def tearDown(self):
        root_logger = logging.getLogger()
        while root_logger.handlers:
            root_logger.removeHandler(root_logger.handlers[0])

        app_logger = logging.getLogger("app.core.logging")
        while app_logger.handlers:
            app_logger.removeHandler(app_logger.handlers[0])

    @patch("app.core.logging.logging.getLogger")
    @patch("app.core.logging.logging.basicConfig")
    def test_setup_logging_default_params(self, mock_basic_config: MagicMock, mock_get_logger: MagicMock):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = setup_logging()

        mock_basic_config.assert_called_once_with(
            level=logging.INFO,
            format="[%(levelname)s][%(name)s]:%(message)s",
            handlers=[mock.ANY],
        )
        mock_get_logger.assert_called_once_with("app.core.logging")
        self.assertEqual(logger, mock_logger)

    @patch("app.core.logging.logging.getLogger")
    @patch("app.core.logging.logging.basicConfig")
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
        mock_get_logger.assert_called_once_with("app.core.logging")
        self.assertEqual(logger, mock_logger)

    def test_logging_format_applied_correctly(self):
        """Интеграционный тест: проверяем, что сообщения логируются в нужном формате."""
        logger = logging.getLogger("app.core.logging")
        root_logger = logging.getLogger()

        while logger.handlers:
            logger.removeHandler(logger.handlers[0])
        while root_logger.handlers:
            root_logger.removeHandler(root_logger.handlers[0])

        log_buffer = StringIO()
        handler = logging.StreamHandler(log_buffer)
        handler.setFormatter(logging.Formatter("[%(levelname)s][%(name)s]:%(message)s"))
        handler.setLevel(logging.INFO)

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        root_logger.setLevel(logging.INFO)
        logger.propagate = False

        test_message = "Test log message"
        logger.info(test_message)
        handler.flush()

        log_output = log_buffer.getvalue().strip()
        expected = f"[INFO][app.core.logging]:{test_message}"
        self.assertEqual(log_output, expected)

    def test_logging_respects_custom_format(self):
        """Проверяем кастомный формат."""
        custom_format = "[LOG] %(levelname)s - %(message)s"
        logger = logging.getLogger("app.core.logging")
        root_logger = logging.getLogger()

        while logger.handlers:
            logger.removeHandler(logger.handlers[0])
        while root_logger.handlers:
            root_logger.removeHandler(root_logger.handlers[0])

        log_buffer = StringIO()
        handler = logging.StreamHandler(log_buffer)
        handler.setFormatter(logging.Formatter(custom_format))
        handler.setLevel(logging.WARNING)

        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        root_logger.setLevel(logging.WARNING)
        logger.propagate = False

        logger.warning("Custom format test")
        handler.flush()

        log_output = log_buffer.getvalue().strip()
        expected = "[LOG] WARNING - Custom format test"
        self.assertEqual(log_output, expected)

    def test_setup_logging_is_idempotent_for_basic_config(self):
        """
        logging.basicConfig игнорируется после первого вызова,
        но наша функция всё равно должна возвращать логгер.
        """
        logger1 = logging.getLogger("app.core.logging")
        root_logger = logging.getLogger()

        while logger1.handlers:
            logger1.removeHandler(logger1.handlers[0])
        while root_logger.handlers:
            root_logger.removeHandler(root_logger.handlers[0])

        log_buffer = StringIO()
        handler = logging.StreamHandler(log_buffer)
        handler.setFormatter(logging.Formatter("[%(levelname)s][%(name)s]:%(message)s"))
        handler.setLevel(logging.INFO)

        logger1.addHandler(handler)
        logger1.setLevel(logging.INFO)
        root_logger.setLevel(logging.INFO)
        logger1.propagate = False

        logger2 = setup_logging(level=logging.DEBUG)
        logger2.setLevel(logging.INFO)
        logger2.propagate = False

        logger1.info("First")
        logger2.error("Second")
        handler.flush()

        output = log_buffer.getvalue()
        self.assertIn("[INFO][app.core.logging]:First", output)
        self.assertIn("[ERROR][app.core.logging]:Second", output)

    def test_kwargs_passed_to_basic_config(self):
        """Проверяем, что **kwargs передаются в basicConfig."""
        with patch("app.core.logging.logging.basicConfig") as mock_basic_config:
            setup_logging(force=True, datefmt="%Y-%m-%d")
            mock_basic_config.assert_called_once_with(
                level=logging.INFO,
                format="[%(levelname)s][%(name)s]:%(message)s",
                handlers=[mock.ANY],
                force=True,
                datefmt="%Y-%m-%d",
            )
