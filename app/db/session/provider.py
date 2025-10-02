import logging

from .manager import Manager
from app.db.types import DatabaseSession
from app.secrets import DATABASE_URL

logger = logging.getLogger(__name__)

manager = Manager(logger=logger, database_url=DATABASE_URL)


def get_db() -> DatabaseSession:
    """Метод Dependency предоставления сессию базы данных.

    Yields:
        Сессия SQLAlchemy для выполнения запросов.
    """
    yield from manager.get_session()
