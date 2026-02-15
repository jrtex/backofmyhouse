import logging

import pytest
from fastapi.testclient import TestClient


class TestRequestLoggingMiddleware:
    def test_logs_request_info(self, client: TestClient, caplog):
        """Middleware logs method, path, status_code, and duration."""
        with caplog.at_level(logging.INFO, logger="app.middleware.request_logging"):
            client.get("/api/health")

        log_records = [
            r for r in caplog.records if r.message == "request_completed"
        ]
        assert len(log_records) >= 1
        record = log_records[0]
        assert record.method == "GET"
        assert record.path == "/api/health"
        assert record.status_code == 200
        assert hasattr(record, "duration_ms")

    def test_logs_non_existent_route(self, client: TestClient, caplog):
        """Middleware logs 404 requests too."""
        with caplog.at_level(logging.INFO, logger="app.middleware.request_logging"):
            client.get("/api/nonexistent")

        log_records = [
            r for r in caplog.records if r.message == "request_completed"
        ]
        assert len(log_records) >= 1
        record = log_records[0]
        assert record.status_code == 404
