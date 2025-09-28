from pydantic import BaseModel, Field


class HealthcheckErrorSchema(BaseModel):
    description: str = Field(..., description="Описание ошибки")
