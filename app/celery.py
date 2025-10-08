from .config import REDIS_URL
from .services.scheduler.main import CeleryConfigurator

celery = CeleryConfigurator(url=REDIS_URL).exec()
