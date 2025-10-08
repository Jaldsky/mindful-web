from fastapi import APIRouter, HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from ....schemas.errors import CommonErrorSchema, ErrorCode
from ....schemas.healthcheck.healthcheck_response_schema import HealthcheckResponseSchema

router = APIRouter(prefix="/healthcheck", tags=["healthcheck"])


@router.get(
    "",
    response_model=HealthcheckResponseSchema,
    responses={
        HTTP_200_OK: {"description": "Сервис работает корректно"},
        HTTP_503_SERVICE_UNAVAILABLE: {"model": CommonErrorSchema, "description": "Сервис не доступен"},
    },
    summary="Работоспособность сервиса",
    description="Проверка работоспособности сервиса",
)
async def check_service_health():
    try:
        return HealthcheckResponseSchema(
            status_code=HTTP_200_OK,
            description="Service is available",
        )
    except Exception:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail=CommonErrorSchema(
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message="Service is not available",
            ).model_dump(),
        )
