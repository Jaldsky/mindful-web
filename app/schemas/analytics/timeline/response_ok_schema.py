from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class AnalyticsTimelineDomainData(BaseModel):
    """Данные по домену внутри временного бакета."""

    domain: str = Field(..., description="Домен")
    total_seconds: int = Field(..., ge=0, description="Количество секунд активности на домене в бакете")


class AnalyticsTimelineDataPoint(BaseModel):
    """Точка timeline аналитики активности."""

    bucket_start: datetime = Field(..., description="Начало временного бакета (UTC)")
    total_seconds: int = Field(..., ge=0, description="Количество секунд активности в бакете")
    unique_domains: int = Field(..., ge=0, description="Количество уникальных доменов в бакете")
    domains: list[AnalyticsTimelineDomainData] = Field(
        default_factory=list,
        description="Топ доменов по времени активности в бакете",
    )


class AnalyticsTimelineResponseOkSchema(BaseModel):
    """Схема успешного ответа OK для analytics timeline endpoint."""

    code: Literal["OK"] = Field("OK", description="Код статуса")
    message: str = Field(..., description="Сообщение статуса")

    from_date: date = Field(..., description="Начало интервала")
    to_date: date = Field(..., description="Конец интервала")
    granularity: Literal["day", "hour"] = Field(..., description="Гранулярность временных бакетов")
    data: list[AnalyticsTimelineDataPoint] = Field(
        default_factory=list,
        description="Список временных бакетов активности",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": "OK",
                "message": "Usage analytics timeline computed",
                "from_date": "2025-04-05",
                "to_date": "2025-04-05",
                "granularity": "hour",
                "data": [
                    {
                        "bucket_start": "2025-04-05T10:00:00Z",
                        "total_seconds": 1800,
                        "unique_domains": 2,
                        "domains": [
                            {"domain": "docs.google.com", "total_seconds": 1200},
                            {"domain": "youtube.com", "total_seconds": 600},
                        ],
                    },
                    {
                        "bucket_start": "2025-04-05T11:00:00Z",
                        "total_seconds": 900,
                        "unique_domains": 1,
                        "domains": [
                            {"domain": "github.com", "total_seconds": 900},
                        ],
                    },
                ],
            }
        }
