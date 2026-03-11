from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    """Метаинформация пагинации."""

    page: int = Field(..., ge=1, description="Номер страницы")
    per_page: int = Field(..., ge=1, description="Количество элементов на странице")
    total_items: int = Field(..., ge=0, description="Общее количество записей")
    total_pages: int = Field(..., ge=0, description="Общее количество страниц")
    next: str | None = Field(None, description="Ссылка на следующую страницу, null если её нет")
    prev: str | None = Field(None, description="Ссылка на предыдущую страницу, null если её нет")


class DomainUsageData(BaseModel):
    """Данные по доменам."""

    domain: str = Field(..., description="Домен")
    category: str | None = Field(None, description="Категория домена")
    total_seconds: int = Field(..., ge=0, description="Количество секунд активности на домене")


class AnalyticsDomainsResponseOkSchema(BaseModel):
    """Схема успешного ответа OK для доменного analytics endpoint."""

    code: Literal["OK"] = Field("OK", description="Код статуса")
    message: str = Field(..., description="Сообщение статуса")

    from_date: date = Field(..., description="Начало интервала")
    to_date: date = Field(..., description="Конец интервала")
    pagination: PaginationMeta = Field(..., description="Метаданные пагинации")
    data: list[DomainUsageData] = Field(default_factory=list, description="Список агрегатов по доменам")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "OK",
                "message": "Usage analytics computed",
                "from_date": "2025-04-05",
                "to_date": "2025-04-05",
                "pagination": {
                    "total_items": 2,
                    "page": 1,
                    "total_pages": 1,
                    "per_page": 50,
                    "next": None,
                    "prev": None,
                },
                "data": [
                    {"domain": "docs.google.com", "category": "work", "total_seconds": 2100},
                    {"domain": "youtube.com", "category": "entertainment", "total_seconds": 600},
                ],
            }
        }
