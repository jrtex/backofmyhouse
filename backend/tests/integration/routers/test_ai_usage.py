from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.ai_usage_log import AIUsageLog
from app.models.user import User
from app.services.ai_usage_service import AIUsageService


def _create_usage_logs(db: Session, user_id, count=3):
    for i in range(count):
        AIUsageService.log_usage(
            db=db,
            user_id=user_id,
            provider="openai" if i % 2 == 0 else "anthropic",
            model="test-model",
            input_type="image" if i % 2 == 0 else "text",
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            success=True,
            duration_ms=1000,
        )


class TestGetUsageLogsEndpoint:
    def test_requires_admin(self, client: TestClient, auth_headers: dict):
        """Standard user should get 403."""
        response = client.get("/api/ai-usage/logs", headers=auth_headers)
        assert response.status_code == 403

    def test_returns_paginated_results(
        self, client: TestClient, admin_auth_headers: dict, admin_user: User, db: Session
    ):
        _create_usage_logs(db, admin_user.id, 5)
        response = client.get(
            "/api/ai-usage/logs?page=1&page_size=2",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    def test_filters_by_provider(
        self, client: TestClient, admin_auth_headers: dict, admin_user: User, db: Session
    ):
        _create_usage_logs(db, admin_user.id, 4)
        response = client.get(
            "/api/ai-usage/logs?provider=openai",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # indices 0,2 are openai
        assert data["total"] == 2

    def test_empty_result(self, client: TestClient, admin_auth_headers: dict):
        response = client.get("/api/ai-usage/logs", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_requires_auth(self, client: TestClient):
        response = client.get("/api/ai-usage/logs")
        assert response.status_code == 401


class TestGetUsageSummaryEndpoint:
    def test_requires_admin(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/ai-usage/summary", headers=auth_headers)
        assert response.status_code == 403

    def test_returns_summary(
        self, client: TestClient, admin_auth_headers: dict, admin_user: User, db: Session
    ):
        _create_usage_logs(db, admin_user.id, 3)
        response = client.get("/api/ai-usage/summary", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_calls"] == 3
        assert data["total_tokens"] == 900  # 3 * 300
        assert "openai" in data["calls_by_provider"]
        assert "image" in data["calls_by_input_type"]

    def test_empty_summary(self, client: TestClient, admin_auth_headers: dict):
        response = client.get("/api/ai-usage/summary", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_calls"] == 0
        assert data["total_tokens"] == 0


class TestDeleteUsageLogsEndpoint:
    def test_requires_admin(self, client: TestClient, auth_headers: dict):
        response = client.delete(
            "/api/ai-usage/logs?retention_days=30", headers=auth_headers
        )
        assert response.status_code == 403

    def test_deletes_old_entries(
        self, client: TestClient, admin_auth_headers: dict, admin_user: User, db: Session
    ):
        # Create an old log
        old_log = AIUsageLog(
            user_id=admin_user.id,
            provider="openai",
            model="m",
            input_type="image",
            success=True,
            created_at=datetime.utcnow() - timedelta(days=100),
        )
        db.add(old_log)
        db.commit()

        # Create a recent log
        AIUsageService.log_usage(
            db=db, user_id=admin_user.id, provider="openai", model="m",
            input_type="text", success=True,
        )

        response = client.delete(
            "/api/ai-usage/logs?retention_days=30",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] == 1

    def test_requires_retention_days_param(
        self, client: TestClient, admin_auth_headers: dict
    ):
        response = client.delete("/api/ai-usage/logs", headers=admin_auth_headers)
        assert response.status_code == 422
