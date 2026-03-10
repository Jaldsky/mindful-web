from fastapi import APIRouter, Depends, Request
from starlette import status

from ...dependencies import (
    get_actor_id_from_token,
    validate_usage_request_params,
    validate_summary_request_params,
    ActorContext,
)
from ...state_services import get_analytics_usage_service, get_analytics_summary_service
from ....core.pagination import PaginationUrlBuilder
from ....core.localizer import localize_key
from ....schemas.analytics import (
    AnalyticsUsageRequestSchema,
    AnalyticsUsageResponseAcceptedSchema,
    AnalyticsUsageResponseOkSchema,
    AnalyticsUsageUnprocessableEntitySchema,
    AnalyticsUsageInternalServerErrorSchema,
    AnalyticsUsageMethodNotAllowedSchema,
    AnalyticsSummaryRequestSchema,
    AnalyticsSummaryResponseAcceptedSchema,
    AnalyticsSummaryResponseOkSchema,
    AnalyticsSummaryUnprocessableEntitySchema,
    AnalyticsSummaryInternalServerErrorSchema,
    AnalyticsSummaryMethodNotAllowedSchema,
)
from ....schemas.general import ServiceUnavailableSchema

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/usage",
    responses={
        status.HTTP_200_OK: {
            "model": AnalyticsUsageResponseOkSchema,
            "description": "Готовая статистика активности по доменам",
        },
        status.HTTP_202_ACCEPTED: {
            "model": AnalyticsUsageResponseAcceptedSchema,
            "description": "Задача поставлена в очередь, результат будет готов позже",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": AnalyticsUsageMethodNotAllowedSchema,
            "description": "Метод не поддерживается",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": AnalyticsUsageUnprocessableEntitySchema,
            "description": "Ошибка бизнес валидации параметров запроса",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": AnalyticsUsageInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Статистика активности пользователя по доменам",
    description=("Возвращает агрегированную статистику времени активности по доменам."),
)
async def get_usage(
    request: Request,
    actor: ActorContext = Depends(get_actor_id_from_token),
    request_params: AnalyticsUsageRequestSchema = Depends(validate_usage_request_params),
    analytics_usage_service=Depends(get_analytics_usage_service),
) -> AnalyticsUsageResponseOkSchema:
    """Возвращает агрегированную статистику активности по доменам за интервал.

    Args:
        request: HTTP-запрос.
        actor: Контекст пользователя или анонимной сессии из JWT.
        request_params: Валидированные параметры from, to, page.
        analytics_usage_service: Сервис аналитики.

    Returns:
        Данные по доменам и пагинация AnalyticsUsageResponseOkSchema.

    Raises:
        OrchestratorTimeoutException: Таймаут задачи (хендлер возвращает 202).
        OrchestratorBrokerUnavailableException: Брокер недоступен (хендлер возвращает 503).
    """
    response = await analytics_usage_service.exec(
        user_id=actor.actor_id,
        from_date=request_params.from_date,
        to_date=request_params.to_date,
        page=request_params.page,
    )
    response.message = localize_key(
        request,
        "analytics.messages.usage_computed",
        "Usage analytics computed",
    )
    response.pagination = PaginationUrlBuilder.build_links(request, response.pagination)

    return response


@router.get(
    "/summary",
    responses={
        status.HTTP_200_OK: {
            "model": AnalyticsSummaryResponseOkSchema,
            "description": "Сводные метрики активности за период",
        },
        status.HTTP_202_ACCEPTED: {
            "model": AnalyticsSummaryResponseAcceptedSchema,
            "description": "Задача поставлена в очередь, результат будет готов позже",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": AnalyticsSummaryMethodNotAllowedSchema,
            "description": "Метод не поддерживается",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": AnalyticsSummaryUnprocessableEntitySchema,
            "description": "Ошибка бизнес валидации параметров запроса",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": AnalyticsSummaryInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Сводная аналитика активности пользователя",
    description=("Возвращает сводные метрики времени активности за заданный интервал."),
)
async def get_summary(
    request: Request,
    actor: ActorContext = Depends(get_actor_id_from_token),
    request_params: AnalyticsSummaryRequestSchema = Depends(validate_summary_request_params),
    analytics_summary_service=Depends(get_analytics_summary_service),
) -> AnalyticsSummaryResponseOkSchema:
    """Возвращает summary статистики активности по доменам за интервал.

    Args:
        request: HTTP-запрос.
        actor: Контекст пользователя или анонимной сессии из JWT.
        request_params: Валидированные параметры from, to.
        analytics_summary_service: Сервис summary аналитики.

    Returns:
        Сводные данные AnalyticsSummaryResponseOkSchema.
    """
    response = await analytics_summary_service.exec(
        user_id=actor.actor_id,
        from_date=request_params.from_date,
        to_date=request_params.to_date,
    )
    response.message = localize_key(
        request,
        "analytics.messages.summary_computed",
        "Usage analytics summary computed",
    )
    return response
