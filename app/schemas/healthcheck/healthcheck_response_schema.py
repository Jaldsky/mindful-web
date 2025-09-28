from pydantic import BaseModel, Field


class HealthcheckResponseSchema(BaseModel):
    status_code: int = Field(..., description="Код статуса")
    description: str = Field(..., description="Описание статуса")
