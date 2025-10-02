import unittest
from unittest.mock import patch, Mock
from urllib.parse import urlparse
from logging import Logger

from sqlalchemy.exc import ArgumentError, SQLAlchemyError

from ...db.exceptions import DatabaseManagerException, DatabaseManagerMessages
from app.db.session.manager import ManagerValidator, Manager


class TestManagerValidator(unittest.TestCase):
    """Тесты для класса ManagerValidator."""

    def test_valid_postgresql_url(self):
        """Проверка корректного PostgreSQL URL."""
        url = "postgresql://user:pass@localhost:5432/mydb"
        validator = ManagerValidator(url)
        self.assertEqual(validator._database_url, url)

    def test_valid_sqlite_file_url(self):
        """Проверка корректного SQLite URL (файл)."""
        url = "sqlite:///test.db"
        validator = ManagerValidator(url)
        self.assertEqual(validator._database_url, url)

    def test_valid_sqlite_memory_url(self):
        """Проверка корректного SQLite in-memory URL."""
        url = "sqlite:///:memory:"
        validator = ManagerValidator(url)
        self.assertEqual(validator._database_url, url)

    def test_valid_mysql_url(self):
        """Проверка корректного MySQL URL."""
        url = "mysql://user:pass@localhost/mydb"
        validator = ManagerValidator(url)
        self.assertEqual(validator._database_url, url)

    def test_valid_postgres_alias_url(self):
        """Проверка схемы 'postgres' как алиаса для 'postgresql'."""
        url = "postgres://user:pass@localhost/mydb"
        validator = ManagerValidator(url)
        self.assertEqual(validator._database_url, url)

    def test_other_supported_schemes(self):
        """Проверка остальных поддерживаемых схем: oracle, mssql, mariadb."""
        for scheme in ["oracle", "mssql", "mariadb"]:
            with self.subTest(scheme=scheme):
                url = f"{scheme}://user:pass@localhost/mydb"
                validator = ManagerValidator(url)
                self.assertEqual(validator._database_url, url)

    def test_invalid_url_type_raises_exception(self):
        """Передача не-строки должна вызывать исключение."""
        with self.assertRaises(DatabaseManagerException) as cm:
            ManagerValidator(123)
        self.assertEqual(str(cm.exception), DatabaseManagerMessages.INVALID_URL_TYPE_ERROR)

    def test_empty_url_raises_exception(self):
        """Пустая строка должна вызывать исключение."""
        with self.assertRaises(DatabaseManagerException) as cm:
            ManagerValidator("")
        self.assertEqual(str(cm.exception), DatabaseManagerMessages.EMPTY_URL_ERROR)

    def test_whitespace_only_url_raises_exception(self):
        """Строка из пробелов должна вызывать исключение."""
        with self.assertRaises(DatabaseManagerException) as cm:
            ManagerValidator("   ")
        self.assertEqual(str(cm.exception), DatabaseManagerMessages.EMPTY_URL_ERROR)

    def test_missing_scheme_raises_exception(self):
        """URL без схемы (например, 'localhost/db') недопустим."""
        with self.assertRaises(DatabaseManagerException) as cm:
            ManagerValidator("localhost/mydb")
        self.assertEqual(str(cm.exception), DatabaseManagerMessages.MISSING_SCHEME_ERROR)

    def test_unsupported_scheme_raises_exception(self):
        """Неподдерживаемая схема (например, 'mongodb') недопустима."""
        unsupported_url = "mongodb://localhost/test"
        with self.assertRaises(DatabaseManagerException) as cm:
            ManagerValidator(unsupported_url)

        parsed = urlparse(unsupported_url)
        expected_message = DatabaseManagerMessages.UNSUPPORTED_SCHEME_ERROR.format(
            scheme=parsed.scheme, supported=", ".join(sorted(ManagerValidator.SUPPORTED_SCHEMES))
        )
        self.assertEqual(str(cm.exception), expected_message)

    def test_invalid_sqlite_format_with_netloc_and_no_path(self):
        """SQLite URL вида 'sqlite://host' без пути — недопустим."""
        with self.assertRaises(DatabaseManagerException) as cm:
            ManagerValidator("sqlite://somehost")
        self.assertEqual(str(cm.exception), DatabaseManagerMessages.INVALID_SQLITE_FORMAT_ERROR)

    def test_sqlite_with_netloc_and_path_is_allowed(self):
        """SQLite с netloc и путём (редко, но допустимо в некоторых контекстах) — не блокируем явно."""
        url = "sqlite://user@host/path/to/db.sqlite"
        validator = ManagerValidator(url)
        self.assertEqual(validator._database_url, url)


class TestManager(unittest.TestCase):
    """Тесты для класса Manager."""

    def setUp(self):
        self.logger = Mock(spec=Logger)
        self.valid_url = "sqlite:///:memory:"

    @patch.object(ManagerValidator, "_validate")
    @patch("app.db.manager.create_engine")
    @patch("app.db.manager.sessionmaker")
    def test_manager_initialization_success(self, mock_sessionmaker, mock_create_engine, mock_validate):
        """Успешная инициализация менеджера."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        mock_session_factory = Mock()
        mock_sessionmaker.return_value = mock_session_factory

        manager = Manager(logger=self.logger, database_url=self.valid_url)

        mock_create_engine.assert_called_once_with(self.valid_url, pool_pre_ping=True)
        mock_sessionmaker.assert_called_once_with(autocommit=False, autoflush=False, bind=mock_engine)
        self.assertEqual(manager._engine, mock_engine)
        self.assertEqual(manager._sessionmaker, mock_session_factory)
        mock_validate.assert_called_once()

    @patch.object(ManagerValidator, "_validate")
    @patch("app.db.manager.create_engine")
    def test_manager_engine_creation_argument_error(self, mock_create_engine, _):
        """Ошибка ArgumentError при создании engine."""
        mock_create_engine.side_effect = ArgumentError("Invalid config")

        with self.assertRaises(DatabaseManagerException) as cm:
            Manager(logger=self.logger, database_url=self.valid_url)

        expected_msg = DatabaseManagerMessages.INVALID_ENGINE_CONFIG_ERROR.format(error="Invalid config")
        self.assertEqual(str(cm.exception), expected_msg)
        self.logger.error.assert_called_with(expected_msg)

    @patch.object(ManagerValidator, "_validate")
    @patch("app.db.manager.create_engine")
    def test_manager_engine_creation_generic_error(self, mock_create_engine, _):
        """Общая ошибка при создании engine."""
        mock_create_engine.side_effect = ValueError("Boom!")

        with self.assertRaises(DatabaseManagerException) as cm:
            Manager(logger=self.logger, database_url=self.valid_url)

        expected_msg = DatabaseManagerMessages.ENGINE_CREATION_FAILED_ERROR.format(error="Boom!")
        self.assertEqual(str(cm.exception), expected_msg)
        self.logger.error.assert_called_with(expected_msg)

    @patch.object(ManagerValidator, "_validate")
    @patch("app.db.manager.create_engine")
    @patch("app.db.manager.sessionmaker")
    def test_get_engine_returns_engine(self, mock_sessionmaker, mock_create_engine, _):
        """Метод get_engine возвращает движок."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        mock_sessionmaker.return_value = Mock()

        manager = Manager(logger=self.logger, database_url=self.valid_url)
        engine = manager.get_engine()

        self.assertIs(engine, mock_engine)

    @patch.object(ManagerValidator, "_validate")
    @patch("app.db.manager.create_engine")
    @patch("app.db.manager.sessionmaker")
    def test_get_session_success(self, mock_sessionmaker, mock_create_engine, _):
        """Успешное получение и закрытие сессии."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        mock_session = Mock()
        mock_session_factory = Mock(return_value=mock_session)
        mock_sessionmaker.return_value = mock_session_factory

        manager = Manager(logger=self.logger, database_url=self.valid_url)

        session_gen = manager.get_session()
        session = next(session_gen)

        self.assertIs(session, mock_session)

        with self.assertRaises(StopIteration):
            next(session_gen)

        mock_session.close.assert_called_once()

    @patch.object(ManagerValidator, "_validate")
    @patch("app.db.manager.create_engine")
    def test_sessionmaker_creation_fails(self, mock_create_engine, _):
        """Ошибка при создании sessionmaker."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        with patch("app.db.manager.sessionmaker", side_effect=RuntimeError("Session factory failed")):
            with self.assertRaises(DatabaseManagerException) as cm:
                Manager(logger=self.logger, database_url=self.valid_url)

        expected_msg = DatabaseManagerMessages.ENGINE_CREATION_FAILED_ERROR.format(error="Session factory failed")
        self.assertEqual(str(cm.exception), expected_msg)
        self.logger.error.assert_called_with(expected_msg)

    @patch.object(ManagerValidator, "_validate")
    @patch("app.db.manager.create_engine")
    @patch("app.db.manager.sessionmaker")
    def test_get_session_sqlalchemy_error_handling(self, mock_sessionmaker, mock_create_engine, _):
        """Обработка SQLAlchemyError внутри сессии."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        mock_session = Mock()
        mock_session_factory = Mock(return_value=mock_session)
        mock_sessionmaker.return_value = mock_session_factory

        manager = Manager(logger=self.logger, database_url=self.valid_url)

        session_gen = manager.get_session()
        next(session_gen)

        test_error = SQLAlchemyError("Query failed")

        with self.assertRaises(DatabaseManagerException) as cm:
            session_gen.throw(test_error)

        expected_msg = DatabaseManagerMessages.SESSION_ERROR.format(error="Query failed")
        self.assertEqual(str(cm.exception), expected_msg)

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

        self.logger.error.assert_called_with(expected_msg)

    @patch.object(ManagerValidator, "_validate")
    @patch("app.db.manager.create_engine")
    @patch("app.db.manager.sessionmaker")
    def test_get_session_rollback_fails(self, mock_sessionmaker, mock_create_engine, _):
        """Ошибка при rollback — логируется, но не маскирует основную ошибку."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        mock_session = Mock()
        mock_session.rollback.side_effect = Exception("Rollback crashed")
        mock_session_factory = Mock(return_value=mock_session)
        mock_sessionmaker.return_value = mock_session_factory

        manager = Manager(logger=self.logger, database_url=self.valid_url)

        session_gen = manager.get_session()
        next(session_gen)

        main_error = RuntimeError("Main error")

        with self.assertRaises(DatabaseManagerException) as cm:
            session_gen.throw(main_error)

        expected_main_msg = DatabaseManagerMessages.UNEXPECTED_SESSION_ERROR.format(error="Main error")
        self.assertEqual(str(cm.exception), expected_main_msg)

        mock_session.rollback.assert_called_once()

        expected_rollback_msg = DatabaseManagerMessages.ROLLBACK_FAILED_ERROR.format(error="Rollback crashed")
        self.logger.warning.assert_called_with(expected_rollback_msg)

        mock_session.close.assert_called_once()

    @patch.object(ManagerValidator, "_validate")
    @patch("app.db.manager.create_engine")
    @patch("app.db.manager.sessionmaker")
    def test_get_session_close_fails(self, mock_sessionmaker, mock_create_engine, _):
        """Ошибка при закрытии сессии — логируется."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        mock_session = Mock()
        mock_session.close.side_effect = OSError("Close failed")
        mock_session_factory = Mock(return_value=mock_session)
        mock_sessionmaker.return_value = mock_session_factory

        manager = Manager(logger=self.logger, database_url=self.valid_url)

        session_gen = manager.get_session()
        next(session_gen)

        with self.assertRaises(StopIteration):
            next(session_gen)

        self.logger.warning.assert_called_with(DatabaseManagerMessages.CLOSE_FAILED_ERROR.format(error="Close failed"))
