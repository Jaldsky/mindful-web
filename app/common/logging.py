import logging
import sys


def setup_logging(level=logging.INFO, forma="[%(levelname)s][%(name)s]:%(message)s", **kwargs) -> logging.Logger:
    """Метод настройки базовой конфигурации логирования.

    Args:
        level: Уровень логирования.
        forma: Формат сообщений лога.
        **kwargs: Дополнительные аргументы, передаваемые в logging.basicConfig.

    Returns:
        Логгер текущего модуля.
    """
    logging.basicConfig(level=level, format=forma, handlers=[logging.StreamHandler(sys.stdout)], **kwargs)
    logger = logging.getLogger(__name__)
    return logger
