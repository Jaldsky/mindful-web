from celery import Celery


class CeleryConfigurator:
    def __init__(self, url: str):
        self.redis_url = url

    def exec(self) -> Celery:
        redis_url = self.redis_url
        app = Celery("scheduler", broker=redis_url, backend=redis_url, include=["app.services.scheduler"])

        return app
