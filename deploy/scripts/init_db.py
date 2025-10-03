#!/usr/bin/env python3
"""Скрипт для инициализации базы данных."""

import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("init_db")

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def init_db() -> None:
    from app.db.session.provider import manager  # noqa: F401
    from app.db.models.tables import Base  # noqa: F401
    from app.db.models import tables  # noqa: F401

    engine = manager.get_engine()

    with engine.connect() as conn:
        conn.execute("SELECT 1")
    logger.info("Подключение к базе данных успешно")

    Base.metadata.create_all(bind=engine)
    logger.info("✅ Таблицы успешно созданы")


if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        logger.error("❌ Ошибка при инициализации базы данных: %s", e)
        sys.exit(1)
