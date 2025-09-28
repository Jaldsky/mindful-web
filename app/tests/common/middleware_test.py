from unittest import TestCase
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from app.main import app


class TestMiddleware(TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("app.common.middleware.logger")
    def test_middleware_logs_successful_request(self, mock_logger: MagicMock):
        response = self.client.get("/api/v1/healthcheck")

        assert response.status_code == 200

        # Проверяем, что logger.info вызывался дважды:
        # 1. При входе в запрос
        # 2. При успешном ответе
        assert mock_logger.info.call_count == 2

        request_log = mock_logger.info.call_args_list[0][0][0]
        response_log = mock_logger.info.call_args_list[1][0][0]

        assert "Request: GET http://testserver/api/v1/healthcheck" in request_log
        assert "Response: 200" in response_log
        assert "Method: GET" in response_log
        assert "Duration:" in response_log

    @patch("app.common.middleware.logger")
    def test_middleware_logs_error_request(self, mock_logger: MagicMock):
        response = self.client.get("/non-existent-path")

        assert response.status_code == 404

        assert mock_logger.info.call_count == 2  # вход + выход
        assert mock_logger.error.call_count == 0  # исключения не было

        request_log = mock_logger.info.call_args_list[0][0][0]
        response_log = mock_logger.info.call_args_list[1][0][0]

        assert "Request: GET http://testserver/non-existent-path" in request_log
        assert "Response: 404" in response_log
        assert "Method: GET" in response_log
        assert "URL: http://testserver/non-existent-path" in response_log
        assert "Duration:" in response_log
