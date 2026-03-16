from fastapi import Request
from fastapi.responses import JSONResponse

from ...core.http_responses import method_not_allowed_response
from ...schemas.analytics import (
    AnalyticsDomainsMethodNotAllowedSchema,
    AnalyticsSummaryMethodNotAllowedSchema,
    AnalyticsTimelineMethodNotAllowedSchema,
)


def analytics_usage_method_not_allowed_response(request: Request) -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для GET /analytics/domains.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(request, AnalyticsDomainsMethodNotAllowedSchema, allowed_method="GET")


def analytics_summary_method_not_allowed_response(request: Request) -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для GET /analytics/summary.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(request, AnalyticsSummaryMethodNotAllowedSchema, allowed_method="GET")


def analytics_timeline_method_not_allowed_response(request: Request) -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для GET /analytics/timeline.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(request, AnalyticsTimelineMethodNotAllowedSchema, allowed_method="GET")
