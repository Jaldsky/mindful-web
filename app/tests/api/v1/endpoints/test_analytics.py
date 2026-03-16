import logging
from unittest import TestCase
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from app.main import app
from app.api.dependencies import ActorContext, get_actor_id_from_token
from app.api.state_services import (
    get_analytics_domains_service,
    get_analytics_summary_service,
    get_analytics_timeline_service,
)
from app.schemas import ErrorCode
from app.schemas.analytics.analytics_error_code import AnalyticsErrorCode
from app.schemas.analytics import (
    AnalyticsDomainsResponseOkSchema,
    AnalyticsDomainsResponseAcceptedSchema,
    AnalyticsDomainsMethodNotAllowedSchema,
    AnalyticsDomainsUnprocessableEntitySchema,
    AnalyticsDomainsInternalServerErrorSchema,
    AnalyticsSummaryResponseOkSchema,
    AnalyticsSummaryResponseAcceptedSchema,
    AnalyticsSummaryMethodNotAllowedSchema,
    AnalyticsSummaryUnprocessableEntitySchema,
    AnalyticsSummaryInternalServerErrorSchema,
    AnalyticsTimelineResponseOkSchema,
    AnalyticsTimelineResponseAcceptedSchema,
    AnalyticsTimelineMethodNotAllowedSchema,
    AnalyticsTimelineUnprocessableEntitySchema,
)
from app.schemas.general import ServiceUnavailableSchema
from app.services.scheduler.exceptions import (
    OrchestratorTimeoutException,
    OrchestratorBrokerUnavailableException,
)


class TestAnalyticsDomainsEndpoint(TestCase):
    """Тесты для analytics domains endpoint."""

    def setUp(self):
        """Настройка тестового клиента."""
        logging.disable(logging.CRITICAL)

        self.mock_analytics_service = Mock()
        app.dependency_overrides[get_analytics_domains_service] = lambda: self.mock_analytics_service

        self.client = TestClient(app)
        self.usage_url = "/api/v1/analytics/domains"
        self.user_id = uuid4()
        self.auth_headers = {"Authorization": "Bearer test-token"}
        self.valid_params = {
            "from": "05-04-2025",
            "to": "05-04-2025",
            "page": 1,
        }
        app.dependency_overrides[get_actor_id_from_token] = lambda: ActorContext(
            actor_id=self.user_id,
            actor_type="access",
        )

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_usage_success_response_schema(self):
        """Успешный запрос возвращает статус 200 OK и корректную схему ответа."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total_items": 2,
                "total_pages": 1,
                "next": None,
                "prev": None,
            },
            "data": [
                {"domain": "docs.google.com", "category": "work", "total_seconds": 2100},
                {"domain": "youtube.com", "category": "entertainment", "total_seconds": 600},
            ],
        }
        self.mock_analytics_service.exec = AsyncMock(return_value=AnalyticsDomainsResponseOkSchema(**mock_data))

        response = self.client.get(
            self.usage_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        data = response.json()
        schema = AnalyticsDomainsResponseOkSchema(**data)
        self.assertEqual(schema.code, "OK")
        self.assertEqual(schema.message, "Usage analytics computed")
        self.assertEqual(len(schema.data), 2)

    def test_usage_timeout_exception(self):
        """Таймаут выполнения задачи возвращает статус 202 ACCEPTED."""
        task_id = "test-task-id-123"
        self.mock_analytics_service.exec = AsyncMock(
            side_effect=OrchestratorTimeoutException(
                task_id=task_id,
            )
        )

        response = self.client.get(
            self.usage_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)
        data = response.json()
        schema = AnalyticsDomainsResponseAcceptedSchema(**data)
        self.assertEqual(schema.code, "ACCEPTED")
        self.assertEqual(schema.task_id, task_id)

    def test_usage_broker_unavailable_exception(self):
        """Недоступность брокера возвращает статус 503 SERVICE_UNAVAILABLE."""
        self.mock_analytics_service.exec = AsyncMock(
            side_effect=OrchestratorBrokerUnavailableException(
                key="scheduler.errors.broker_unavailable",
            )
        )

        response = self.client.get(
            self.usage_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_503_SERVICE_UNAVAILABLE)
        data = response.json()
        schema = ServiceUnavailableSchema(**data)
        self.assertEqual(schema.code, ErrorCode.SERVICE_UNAVAILABLE)

    def test_usage_method_not_allowed_different_methods(self):
        """Различные HTTP методы (POST, PUT, DELETE, PATCH) возвращают 405."""
        methods = ["post", "put", "delete", "patch"]
        for method in methods:
            with self.subTest(method=method):
                client_method = getattr(self.client, method)
                response = client_method(
                    self.usage_url,
                    params=self.valid_params,
                    headers=self.auth_headers,
                )
                self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

                data = response.json()
                schema = AnalyticsDomainsMethodNotAllowedSchema(**data)
                self.assertEqual(schema.code, ErrorCode.METHOD_NOT_ALLOWED)

    def test_usage_method_not_allowed_content_type(self):
        """При ошибке 405 возвращается JSON с правильным Content-Type."""
        response = self.client.post(
            self.usage_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.headers["content-type"], "application/json")

    def test_usage_missing_required_params(self):
        """Отсутствие обязательных параметров возвращает 400."""
        # Отсутствует параметр 'from'
        response = self.client.get(
            self.usage_url,
            params={"to": "05-04-2025", "page": 1},
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

        # Отсутствует параметр 'to'
        response = self.client.get(
            self.usage_url,
            params={"from": "05-04-2025", "page": 1},
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_usage_invalid_date_format(self):
        """Неверный формат даты возвращает 422."""
        response = self.client.get(
            self.usage_url,
            params={"from": "invalid-date", "to": "05-04-2025", "page": 1},
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, HTTP_422_UNPROCESSABLE_ENTITY)

        data = response.json()
        schema = AnalyticsDomainsUnprocessableEntitySchema(**data)
        self.assertEqual(schema.code, AnalyticsErrorCode.INVALID_DATE_FORMAT)

    def test_usage_invalid_page_parameter(self):
        """Неверный параметр page (меньше 1) возвращает 400."""
        response = self.client.get(
            self.usage_url,
            params={"from": "05-04-2025", "to": "05-04-2025", "page": 0},
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_usage_supports_anonymous_actor(self):
        """Анонимный актор корректно обрабатывается (UUID передается в сервис)."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total_items": 0,
                "total_pages": 0,
                "next": None,
                "prev": None,
            },
            "data": [],
        }
        app.dependency_overrides[get_actor_id_from_token] = lambda: ActorContext(
            actor_id=self.user_id,
            actor_type="anon",
        )
        self.mock_analytics_service.exec = AsyncMock(return_value=AnalyticsDomainsResponseOkSchema(**mock_data))

        response = self.client.get(
            self.usage_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.mock_analytics_service.exec.assert_called_once()
        call_kwargs = self.mock_analytics_service.exec.call_args.kwargs
        self.assertEqual(call_kwargs.get("user_id"), self.user_id)

    def test_usage_pagination_links(self):
        """Проверка корректного построения ссылок пагинации."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total_items": 100,
                "total_pages": 2,
                "next": None,
                "prev": None,
            },
            "data": [],
        }
        self.mock_analytics_service.exec = AsyncMock(return_value=AnalyticsDomainsResponseOkSchema(**mock_data))

        response = self.client.get(
            self.usage_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        data = response.json()
        schema = AnalyticsDomainsResponseOkSchema(**data)
        self.assertIsNotNone(schema.pagination.next)
        self.assertIsNone(schema.pagination.prev)

    def test_usage_passes_filter_and_sort_params(self):
        """Параметры per_page/sort_by/order/search прокидываются в сервис."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "pagination": {
                "page": 2,
                "per_page": 50,
                "total_items": 0,
                "total_pages": 0,
                "next": None,
                "prev": None,
            },
            "data": [],
        }
        self.mock_analytics_service.exec = AsyncMock(return_value=AnalyticsDomainsResponseOkSchema(**mock_data))

        response = self.client.get(
            self.usage_url,
            params={
                **self.valid_params,
                "page": 2,
                "per_page": 50,
                "sort_by": "domain",
                "order": "asc",
                "search": "youtube",
            },
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        call_kwargs = self.mock_analytics_service.exec.call_args.kwargs
        self.assertEqual(call_kwargs.get("page"), 2)
        self.assertEqual(call_kwargs.get("per_page"), 50)
        self.assertEqual(call_kwargs.get("sort_by"), "domain")
        self.assertEqual(call_kwargs.get("order"), "asc")
        self.assertEqual(call_kwargs.get("search"), "youtube")

    def test_usage_response_content_type(self):
        """Успешный ответ возвращает JSON с правильным Content-Type."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total_items": 0,
                "total_pages": 0,
                "next": None,
                "prev": None,
            },
            "data": [],
        }
        self.mock_analytics_service.exec = AsyncMock(return_value=AnalyticsDomainsResponseOkSchema(**mock_data))

        response = self.client.get(
            self.usage_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers["content-type"], "application/json")

    def test_usage_multiple_requests(self):
        """Множественные запросы работают корректно."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total_items": 0,
                "total_pages": 0,
                "next": None,
                "prev": None,
            },
            "data": [],
        }
        self.mock_analytics_service.exec = AsyncMock(return_value=AnalyticsDomainsResponseOkSchema(**mock_data))

        for _ in range(5):
            response = self.client.get(
                self.usage_url,
                params=self.valid_params,
                headers=self.auth_headers,
            )
            self.assertEqual(response.status_code, HTTP_200_OK)

            data = response.json()
            schema = AnalyticsDomainsResponseOkSchema(**data)
            self.assertEqual(schema.code, "OK")


class TestAnalyticsSummaryEndpoint(TestCase):
    """Тесты для analytics summary endpoint."""

    def setUp(self):
        """Настройка тестового клиента."""
        logging.disable(logging.CRITICAL)

        self.mock_analytics_service = Mock()
        app.dependency_overrides[get_analytics_summary_service] = lambda: self.mock_analytics_service

        self.client = TestClient(app)
        self.summary_url = "/api/v1/analytics/summary"
        self.user_id = uuid4()
        self.auth_headers = {"Authorization": "Bearer test-token"}
        self.valid_params = {
            "from": "05-04-2025",
            "to": "05-04-2025",
        }
        app.dependency_overrides[get_actor_id_from_token] = lambda: ActorContext(
            actor_id=self.user_id,
            actor_type="access",
        )

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_summary_success_response_schema(self):
        """Успешный запрос возвращает статус 200 OK и корректную схему ответа."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics summary computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "data": {
                "total_seconds": 2700,
                "total_domains": 2,
                "avg_seconds_per_domain": 1350,
                "top_domain": "docs.google.com",
                "top_domain_seconds": 2100,
            },
        }
        self.mock_analytics_service.exec = AsyncMock(return_value=AnalyticsSummaryResponseOkSchema(**mock_data))

        response = self.client.get(
            self.summary_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        data = response.json()
        schema = AnalyticsSummaryResponseOkSchema(**data)
        self.assertEqual(schema.code, "OK")
        self.assertEqual(schema.message, "Usage analytics summary computed")
        self.assertEqual(schema.data.total_seconds, 2700)

    def test_summary_method_not_allowed_different_methods(self):
        """Различные HTTP методы (POST, PUT, DELETE, PATCH) возвращают 405."""
        methods = ["post", "put", "delete", "patch"]
        for method in methods:
            with self.subTest(method=method):
                client_method = getattr(self.client, method)
                response = client_method(
                    self.summary_url,
                    params=self.valid_params,
                    headers=self.auth_headers,
                )
                self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

                data = response.json()
                schema = AnalyticsSummaryMethodNotAllowedSchema(**data)
                self.assertEqual(schema.code, ErrorCode.METHOD_NOT_ALLOWED)

    def test_summary_timeout_exception(self):
        """Таймаут выполнения задачи возвращает статус 202 ACCEPTED."""
        task_id = "test-summary-task-id-123"
        self.mock_analytics_service.exec = AsyncMock(
            side_effect=OrchestratorTimeoutException(
                task_id=task_id,
            )
        )

        response = self.client.get(
            self.summary_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)
        data = response.json()
        schema = AnalyticsSummaryResponseAcceptedSchema(**data)
        self.assertEqual(schema.code, "ACCEPTED")
        self.assertEqual(schema.task_id, task_id)

    def test_summary_broker_unavailable_exception(self):
        """Недоступность брокера возвращает статус 503 SERVICE_UNAVAILABLE."""
        self.mock_analytics_service.exec = AsyncMock(
            side_effect=OrchestratorBrokerUnavailableException(
                key="scheduler.errors.broker_unavailable",
            )
        )

        response = self.client.get(
            self.summary_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_503_SERVICE_UNAVAILABLE)
        data = response.json()
        schema = ServiceUnavailableSchema(**data)
        self.assertEqual(schema.code, ErrorCode.SERVICE_UNAVAILABLE)

    def test_summary_method_not_allowed_content_type(self):
        """При ошибке 405 возвращается JSON с правильным Content-Type."""
        response = self.client.post(
            self.summary_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.headers["content-type"], "application/json")

    def test_summary_missing_required_params(self):
        """Отсутствие обязательных параметров возвращает 400."""
        response = self.client.get(
            self.summary_url,
            params={"to": "05-04-2025"},
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

        response = self.client.get(
            self.summary_url,
            params={"from": "05-04-2025"},
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_summary_invalid_date_format(self):
        """Неверный формат даты возвращает 422."""
        response = self.client.get(
            self.summary_url,
            params={"from": "invalid-date", "to": "05-04-2025"},
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, HTTP_422_UNPROCESSABLE_ENTITY)

        data = response.json()
        schema = AnalyticsSummaryUnprocessableEntitySchema(**data)
        self.assertEqual(schema.code, AnalyticsErrorCode.INVALID_DATE_FORMAT)

    def test_summary_supports_anonymous_actor(self):
        """Анонимный актор корректно обрабатывается (UUID передается в сервис)."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics summary computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "data": {
                "total_seconds": 0,
                "total_domains": 0,
                "avg_seconds_per_domain": 0,
                "top_domain": None,
                "top_domain_seconds": 0,
            },
        }
        app.dependency_overrides[get_actor_id_from_token] = lambda: ActorContext(
            actor_id=self.user_id,
            actor_type="anon",
        )
        self.mock_analytics_service.exec = AsyncMock(return_value=AnalyticsSummaryResponseOkSchema(**mock_data))

        response = self.client.get(
            self.summary_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.mock_analytics_service.exec.assert_called_once()
        call_kwargs = self.mock_analytics_service.exec.call_args.kwargs
        self.assertEqual(call_kwargs.get("user_id"), self.user_id)

    def test_summary_response_content_type(self):
        """Успешный ответ возвращает JSON с правильным Content-Type."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics summary computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "data": {
                "total_seconds": 0,
                "total_domains": 0,
                "avg_seconds_per_domain": 0,
                "top_domain": None,
                "top_domain_seconds": 0,
            },
        }
        self.mock_analytics_service.exec = AsyncMock(return_value=AnalyticsSummaryResponseOkSchema(**mock_data))

        response = self.client.get(
            self.summary_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers["content-type"], "application/json")

    def test_summary_multiple_requests(self):
        """Множественные запросы работают корректно."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics summary computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "data": {
                "total_seconds": 0,
                "total_domains": 0,
                "avg_seconds_per_domain": 0,
                "top_domain": None,
                "top_domain_seconds": 0,
            },
        }
        self.mock_analytics_service.exec = AsyncMock(return_value=AnalyticsSummaryResponseOkSchema(**mock_data))

        for _ in range(5):
            response = self.client.get(
                self.summary_url,
                params=self.valid_params,
                headers=self.auth_headers,
            )
            self.assertEqual(response.status_code, HTTP_200_OK)

            data = response.json()
            schema = AnalyticsSummaryResponseOkSchema(**data)
            self.assertEqual(schema.code, "OK")


class TestAnalyticsTimelineEndpoint(TestCase):
    """Тесты для analytics timeline endpoint."""

    def setUp(self):
        """Настройка тестового клиента."""
        logging.disable(logging.CRITICAL)

        self.mock_analytics_service = Mock()
        app.dependency_overrides[get_analytics_timeline_service] = lambda: self.mock_analytics_service

        self.client = TestClient(app)
        self.timeline_url = "/api/v1/analytics/timeline"
        self.user_id = uuid4()
        self.auth_headers = {"Authorization": "Bearer test-token"}
        self.valid_params = {
            "from": "05-04-2025",
            "to": "05-04-2025",
            "granularity": "day",
            "top_domains_limit": 5,
        }
        app.dependency_overrides[get_actor_id_from_token] = lambda: ActorContext(
            actor_id=self.user_id,
            actor_type="access",
        )

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_timeline_success_response_schema(self):
        """Успешный запрос возвращает статус 200 OK и корректную схему ответа."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics timeline computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "granularity": "day",
            "data": [
                {
                    "bucket_start": "2025-04-05T00:00:00Z",
                    "total_seconds": 2700,
                    "unique_domains": 2,
                    "domains": [
                        {"domain": "docs.google.com", "total_seconds": 2100},
                        {"domain": "youtube.com", "total_seconds": 600},
                    ],
                }
            ],
        }
        self.mock_analytics_service.exec = AsyncMock(return_value=AnalyticsTimelineResponseOkSchema(**mock_data))

        response = self.client.get(
            self.timeline_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        data = response.json()
        schema = AnalyticsTimelineResponseOkSchema(**data)
        self.assertEqual(schema.code, "OK")
        self.assertEqual(schema.granularity, "day")
        self.assertEqual(len(schema.data), 1)

    def test_timeline_timeout_exception(self):
        """Таймаут выполнения задачи возвращает статус 202 ACCEPTED."""
        task_id = "test-timeline-task-id-123"
        self.mock_analytics_service.exec = AsyncMock(
            side_effect=OrchestratorTimeoutException(
                task_id=task_id,
            )
        )

        response = self.client.get(
            self.timeline_url,
            params=self.valid_params,
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)
        data = response.json()
        schema = AnalyticsTimelineResponseAcceptedSchema(**data)
        self.assertEqual(schema.code, "ACCEPTED")
        self.assertEqual(schema.task_id, task_id)

    def test_timeline_method_not_allowed_different_methods(self):
        """Различные HTTP методы (POST, PUT, DELETE, PATCH) возвращают 405."""
        methods = ["post", "put", "delete", "patch"]
        for method in methods:
            with self.subTest(method=method):
                client_method = getattr(self.client, method)
                response = client_method(
                    self.timeline_url,
                    params=self.valid_params,
                    headers=self.auth_headers,
                )
                self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

                data = response.json()
                schema = AnalyticsTimelineMethodNotAllowedSchema(**data)
                self.assertEqual(schema.code, ErrorCode.METHOD_NOT_ALLOWED)

    def test_timeline_invalid_date_format(self):
        """Неверный формат даты возвращает 422."""
        response = self.client.get(
            self.timeline_url,
            params={"from": "invalid-date", "to": "05-04-2025", "granularity": "day"},
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, HTTP_422_UNPROCESSABLE_ENTITY)

        data = response.json()
        schema = AnalyticsTimelineUnprocessableEntitySchema(**data)
        self.assertEqual(schema.code, AnalyticsErrorCode.INVALID_DATE_FORMAT)

    def test_timeline_passes_granularity_param(self):
        """Параметры granularity и top_domains_limit прокидываются в сервис."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics timeline computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "granularity": "hour",
            "data": [],
        }
        self.mock_analytics_service.exec = AsyncMock(return_value=AnalyticsTimelineResponseOkSchema(**mock_data))

        response = self.client.get(
            self.timeline_url,
            params={
                "from": "05-04-2025",
                "to": "05-04-2025",
                "granularity": "hour",
                "top_domains_limit": 3,
            },
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        call_kwargs = self.mock_analytics_service.exec.call_args.kwargs
        self.assertEqual(call_kwargs.get("granularity"), "hour")
        self.assertEqual(call_kwargs.get("top_domains_limit"), 3)

    def test_timeline_hourly_range_too_large(self):
        """Слишком большой диапазон для hour-гранулярности возвращает 422."""
        response = self.client.get(
            self.timeline_url,
            params={"from": "01-01-2025", "to": "31-12-2025", "granularity": "hour"},
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, HTTP_422_UNPROCESSABLE_ENTITY)

        data = response.json()
        schema = AnalyticsTimelineUnprocessableEntitySchema(**data)
        self.assertEqual(schema.code, AnalyticsErrorCode.INVALID_TIME_RANGE)

    def test_timeline_daily_range_too_large(self):
        """Слишком большой диапазон для day-гранулярности возвращает 422."""
        response = self.client.get(
            self.timeline_url,
            params={"from": "01-01-2025", "to": "31-12-2999", "granularity": "day"},
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, HTTP_422_UNPROCESSABLE_ENTITY)

        data = response.json()
        schema = AnalyticsTimelineUnprocessableEntitySchema(**data)
        self.assertEqual(schema.code, AnalyticsErrorCode.INVALID_TIME_RANGE)
