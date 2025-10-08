import logging

from .manager import Manager
from ...config import DATABASE_URL

logger = logging.getLogger(__name__)

manager = Manager(logger=logger, database_url=DATABASE_URL)
