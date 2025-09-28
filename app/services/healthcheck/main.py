from app.common import StringEnum


class HealthStatus(StringEnum):
    OK = "Сервис доступен"
    SERVICE_UNAVAILABLE = "Сервис не доступен"
