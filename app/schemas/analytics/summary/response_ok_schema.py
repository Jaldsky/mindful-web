from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AnalyticsSummaryData(BaseModel):
    """Сводные метрики активности за интервал."""

    total_seconds: int = Field(..., ge=0, description="Общее количество секунд активности")
    total_domains: int = Field(..., ge=0, description="Количество уникальных доменов")
    avg_seconds_per_domain: int = Field(..., ge=0, description="Среднее количество секунд на домен")
    top_domain: str | None = Field(None, description="Домен с максимальным временем активности")
    top_domain_seconds: int = Field(..., ge=0, description="Количество секунд активности на top-домене")


class AnalyticsSummaryResponseOkSchema(BaseModel):
    """Схема успешного ответа OK для analytics summary endpoint."""

    code: Literal["OK"] = Field("OK", description="Код статуса")
    message: str = Field(..., description="Сообщение статуса")

    from_date: date = Field(..., description="Начало интервала")
    to_date: date = Field(..., description="Конец интервала")
    data: AnalyticsSummaryData = Field(..., description="Сводные метрики за период")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "OK",
                "message": "Usage analytics summary computed",
                "from_date": "2025-04-05",
                "to_date": "2025-04-05",
                "data": {
                    "total_seconds": 2700,
                    "total_domains": 2,
                    "avg_seconds_per_domain": 1350,
                    "top_domain": "docs.google.com",
                    "top_domain_seconds": 2100,
                },
            }
        }
