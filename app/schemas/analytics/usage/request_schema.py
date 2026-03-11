from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class AnalyticsDomainsRequestSchema(BaseModel):
    """Схема запроса для получения статистики по доменам."""

    from_date: date = Field(..., description="Начало интервала")
    to_date: date = Field(..., description="Конец интервала")
    page: int = Field(default=1, description="Номер страницы")
    per_page: int = Field(default=20, description="Количество элементов на странице")
    sort_by: Literal["total_seconds", "domain", "category"] = Field(
        default="total_seconds",
        description="Поле сортировки",
    )
    order: Literal["asc", "desc"] = Field(default="desc", description="Направление сортировки")
    search: str | None = Field(default=None, description="Поиск по домену (подстрока)")

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
    def validate_time_range(self) -> "AnalyticsDomainsRequestSchema":
        """Валидация временного диапазона (422)."""
        from ....services.analytics.validators import AnalyticsServiceValidators

        AnalyticsServiceValidators.validate_time_range(self.from_date, self.to_date)
        return self

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        """Валидация номера страницы."""
        from ....services.analytics.validators import AnalyticsServiceValidators

        AnalyticsServiceValidators.validate_page(v)
        return v

    @field_validator("per_page")
    @classmethod
    def validate_per_page(cls, v: int) -> int:
        """Валидация размера страницы."""
        from ....services.analytics.validators import AnalyticsServiceValidators

        AnalyticsServiceValidators.validate_per_page(v)
        return v

    @field_validator("sort_by", "order", mode="before")
    @classmethod
    def normalize_sort_values(cls, v: Any) -> Any:
        """Нормализация параметров сортировки."""
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("search", mode="before")
    @classmethod
    def normalize_search(cls, v: Any) -> Any:
        """Нормализация поисковой строки."""
        if v is None:
            return None
        if not isinstance(v, str):
            return v
        value = v.strip()
        return value or None

    class Config:
        json_schema_extra = {
            "example": {
                "from": "05-04-2025",
                "to": "05-04-2025",
                "page": 1,
                "per_page": 20,
                "sort_by": "total_seconds",
                "order": "desc",
                "search": "google",
            }
        }
