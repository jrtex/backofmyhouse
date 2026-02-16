from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.models.ai_usage_log import AIUsageLog
from app.models.user import User
from app.services.ai_usage_service import AIUsageService
from tests.conftest import create_test_user


class TestLogUsage:
    def test_creates_db_record(self, db: Session, test_user: User):
        result = AIUsageService.log_usage(
            db=db,
            user_id=test_user.id,
            provider="openai",
            model="gpt-4o-mini",
            input_type="image",
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            success=True,
            duration_ms=1500,
        )
        assert result is not None
        assert result.provider == "openai"
        assert result.model == "gpt-4o-mini"
        assert result.input_type == "image"
        assert result.input_tokens == 100
        assert result.output_tokens == 200
        assert result.total_tokens == 300
        assert result.success is True
        assert result.duration_ms == 1500
        assert result.user_id == test_user.id

    def test_creates_failure_record(self, db: Session):
        result = AIUsageService.log_usage(
            db=db,
            user_id=None,
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            input_type="text",
            success=False,
            error_message="Extraction failed",
        )
        assert result is not None
        assert result.success is False
        assert result.error_message == "Extraction failed"

    def test_handles_null_user_id(self, db: Session):
        result = AIUsageService.log_usage(
            db=db,
            user_id=None,
            provider="gemini",
            model="gemini-2.0-flash",
            input_type="url",
            success=True,
        )
        assert result is not None
        assert result.user_id is None

    def test_does_not_raise_on_db_error(self, db: Session):
        """log_usage should never raise - catches and logs exceptions."""
        with patch.object(db, "commit", side_effect=Exception("DB write failed")):
            result = AIUsageService.log_usage(
                db=db,
                user_id=None,
                provider="openai",
                model="gpt-4o-mini",
                input_type="image",
                success=True,
            )
        assert result is None


class TestGetUsageLogs:
    def _create_logs(self, db: Session, count: int = 5):
        for i in range(count):
            AIUsageService.log_usage(
                db=db,
                user_id=None,
                provider="openai" if i % 2 == 0 else "anthropic",
                model="test-model",
                input_type="image" if i % 2 == 0 else "text",
                total_tokens=100 * (i + 1),
                success=True,
            )

    def test_returns_paginated_results(self, db: Session):
        self._create_logs(db, 5)
        result = AIUsageService.get_usage_logs(db, page=1, page_size=2)
        assert result.total == 5
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 2

    def test_second_page(self, db: Session):
        self._create_logs(db, 5)
        result = AIUsageService.get_usage_logs(db, page=2, page_size=2)
        assert len(result.items) == 2
        assert result.total == 5

    def test_filter_by_provider(self, db: Session):
        self._create_logs(db, 5)
        result = AIUsageService.get_usage_logs(db, provider="openai")
        # 5 logs: indices 0,2,4 are openai
        assert result.total == 3

    def test_filter_by_user_id(self, db: Session, test_user: User):
        # Create logs for test_user
        for _ in range(3):
            AIUsageService.log_usage(
                db=db, user_id=test_user.id, provider="openai",
                model="m", input_type="text", success=True,
            )
        # Create logs for a different user
        other_user = create_test_user(
            db, username="other", email="other@example.com",
        )
        AIUsageService.log_usage(
            db=db, user_id=other_user.id, provider="openai",
            model="m", input_type="text", success=True,
        )
        result = AIUsageService.get_usage_logs(db, user_id=test_user.id)
        assert result.total == 3

    def test_filter_by_date_range(self, db: Session):
        self._create_logs(db, 3)
        now = datetime.utcnow()
        result = AIUsageService.get_usage_logs(
            db,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
        )
        assert result.total == 3

    def test_empty_result(self, db: Session):
        result = AIUsageService.get_usage_logs(db)
        assert result.total == 0
        assert result.items == []


class TestGetUsageSummary:
    def test_aggregates_correctly(self, db: Session):
        AIUsageService.log_usage(
            db=db, user_id=None, provider="openai", model="m",
            input_type="image", total_tokens=100, success=True,
        )
        AIUsageService.log_usage(
            db=db, user_id=None, provider="openai", model="m",
            input_type="text", total_tokens=200, success=True,
        )
        AIUsageService.log_usage(
            db=db, user_id=None, provider="anthropic", model="m",
            input_type="image", total_tokens=300, success=True,
        )

        summary = AIUsageService.get_usage_summary(db)
        assert summary.total_calls == 3
        assert summary.total_tokens == 600
        assert summary.calls_by_provider == {"openai": 2, "anthropic": 1}
        assert summary.calls_by_input_type == {"image": 2, "text": 1}

    def test_empty_summary(self, db: Session):
        summary = AIUsageService.get_usage_summary(db)
        assert summary.total_calls == 0
        assert summary.total_tokens == 0
        assert summary.calls_by_provider == {}
        assert summary.calls_by_input_type == {}

    def test_date_range_filter(self, db: Session):
        AIUsageService.log_usage(
            db=db, user_id=None, provider="openai", model="m",
            input_type="image", total_tokens=100, success=True,
        )
        now = datetime.utcnow()
        summary = AIUsageService.get_usage_summary(
            db, start_date=now - timedelta(hours=1), end_date=now + timedelta(hours=1)
        )
        assert summary.total_calls == 1
        assert summary.period_start is not None
        assert summary.period_end is not None


class TestCleanupOldLogs:
    def test_deletes_old_records(self, db: Session):
        # Create an old log entry
        old_log = AIUsageLog(
            user_id=None,
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
            db=db, user_id=None, provider="openai", model="m",
            input_type="text", success=True,
        )

        deleted = AIUsageService.cleanup_old_logs(db, retention_days=90)
        assert deleted == 1

        remaining = db.query(AIUsageLog).count()
        assert remaining == 1

    def test_keeps_recent_records(self, db: Session):
        AIUsageService.log_usage(
            db=db, user_id=None, provider="openai", model="m",
            input_type="image", success=True,
        )
        deleted = AIUsageService.cleanup_old_logs(db, retention_days=90)
        assert deleted == 0
        assert db.query(AIUsageLog).count() == 1
