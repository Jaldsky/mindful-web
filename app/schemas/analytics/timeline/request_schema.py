from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class AnalyticsTimelineRequestSchema(BaseModel):
    """Схема запроса для получения timeline аналитики использования."""

    from_date: date = Field(..., description="Начало интервала")
    to_date: date = Field(..., description="Конец интервала")
    granularity: Literal["day", "hour"] = Field(
        default="day",
        description="Гранулярность временных бакетов",
    )
    top_domains_limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Максимум доменов в каждом бакете",
    )

    @field_validator("from_date", "to_date", mode="before")
    @classmethod
    def normalize_date(cls, v: Any) -> Any:
        """Нормализация даты."""
        if not isinstance(v, str):
            return v
        from ....services.analytics.normalizers import AnalyticsServiceNormalizers

        return AnalyticsServiceNormalizers.normalize_date(v)

    @field_validator("from_date", "to_date", mode="before")
    @classmethod
    def validate_date(cls, v: Any) -> date:
        """Валидация даты (422)."""
        from ....services.analytics.validators import AnalyticsServiceValidators

        return AnalyticsServiceValidators.validate_date(v)

    @model_validator(mode="after")
    def validate_time_range(self) -> "AnalyticsTimelineRequestSchema":
        """Валидация временного диапазона (422)."""
        from ....services.analytics.validators import AnalyticsServiceValidators

        AnalyticsServiceValidators.validate_time_range(self.from_date, self.to_date)
        AnalyticsServiceValidators.validate_timeline_time_range(
            self.from_date,
            self.to_date,
            self.granularity,
        )
        return self

    @field_validator("granularity", mode="before")
    @classmethod
    def normalize_granularity(cls, v: Any) -> Any:
        """Нормализация параметра granularity."""
        if isinstance(v, str):
            return v.strip().lower()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "from": "05-04-2025",
                "to": "05-04-2025",
                "granularity": "hour",
                "top_domains_limit": 5,
            }
        }
