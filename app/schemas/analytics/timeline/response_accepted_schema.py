from typing import Literal

from pydantic import BaseModel, Field


class AnalyticsTimelineResponseAcceptedSchema(BaseModel):
    """Схема успешного ответа ACCEPTED для analytics timeline endpoint."""

    code: Literal["ACCEPTED"] = Field("ACCEPTED", description="Код статуса")
    message: str = Field(..., description="Сообщение статуса")

    task_id: str = Field(..., description="Идентификатор Celery задачи")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "ACCEPTED",
                "message": "Task accepted",
                "task_id": "f1c9b8b6-0a54-4a2c-a6e0-2dcb8baf3b73",
            }
        }
