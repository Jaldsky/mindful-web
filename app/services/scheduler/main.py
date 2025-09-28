from celery import Celery


class CeleryConfigurator:
    def __init__(self, url: str, database: int = 0):
        self.redis_url = f"{url}/{database}"

    def exec(self) -> Celery:
        redis_url = self.redis_url
        app = Celery("scheduler", broker=redis_url, backend=redis_url, include=["app.services.scheduler"])

        return app
