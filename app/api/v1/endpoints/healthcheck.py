from fastapi import APIRouter, HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from ....schemas.healthcheck.healthcheck_error_schema import HealthcheckErrorSchema
from ....schemas.healthcheck.healthcheck_response_schema import HealthcheckResponseSchema
from ....services.healthcheck.main import HealthStatus

router = APIRouter(prefix="/healthcheck", tags=["healthcheck"])


@router.get(
    "",
    response_model=HealthcheckResponseSchema,
    responses={
        HTTP_200_OK: {"description": "Сервис работает корректно"},
        HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthcheckErrorSchema, "description": "Сервис не доступен"},
    },
    summary="Работоспособность сервиса",
    description="Проверка работоспособности сервиса",
)
async def check_service_health():
    try:
        return HealthcheckResponseSchema(
            status_code=HTTP_200_OK,
            description=HealthStatus.OK,
        )
    except Exception:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail=HealthcheckErrorSchema(
                description=HealthStatus.SERVICE_UNAVAILABLE,
            ).model_dump(),
        )
