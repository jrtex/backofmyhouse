import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ai_usage_log import AIUsageLog
from app.schemas.ai_usage import AIUsageLogList, AIUsageLogResponse, AIUsageSummary

logger = logging.getLogger(__name__)


class AIUsageService:
    @staticmethod
    def log_usage(
        db: Session,
        user_id: Optional[UUID],
        provider: str,
        model: str,
        input_type: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> Optional[AIUsageLog]:
        try:
            log_entry = AIUsageLog(
                user_id=user_id,
                provider=provider,
                model=model,
                input_type=input_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                success=success,
                error_message=error_message,
                duration_ms=duration_ms,
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry
        except Exception:
            logger.exception("Failed to log AI usage")
            db.rollback()
            return None

    @staticmethod
    def get_usage_logs(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[UUID] = None,
        provider: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AIUsageLogList:
        query = db.query(AIUsageLog)

        if user_id is not None:
            query = query.filter(AIUsageLog.user_id == user_id)
        if provider is not None:
            query = query.filter(AIUsageLog.provider == provider)
        if start_date is not None:
            query = query.filter(AIUsageLog.created_at >= start_date)
        if end_date is not None:
            query = query.filter(AIUsageLog.created_at <= end_date)

        total = query.count()
        offset = (page - 1) * page_size
        items = (
            query.order_by(AIUsageLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return AIUsageLogList(
            items=[AIUsageLogResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def get_usage_summary(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AIUsageSummary:
        query = db.query(AIUsageLog)

        if start_date is not None:
            query = query.filter(AIUsageLog.created_at >= start_date)
        if end_date is not None:
            query = query.filter(AIUsageLog.created_at <= end_date)

        total_calls = query.count()
        total_tokens = (
            db.query(func.coalesce(func.sum(AIUsageLog.total_tokens), 0))
            .filter(
                *([AIUsageLog.created_at >= start_date] if start_date else []),
                *([AIUsageLog.created_at <= end_date] if end_date else []),
            )
            .scalar()
        )

        # Calls by provider
        provider_rows = (
            query.with_entities(AIUsageLog.provider, func.count())
            .group_by(AIUsageLog.provider)
            .all()
        )
        calls_by_provider = {row[0]: row[1] for row in provider_rows}

        # Calls by input type
        input_type_rows = (
            query.with_entities(AIUsageLog.input_type, func.count())
            .group_by(AIUsageLog.input_type)
            .all()
        )
        calls_by_input_type = {row[0]: row[1] for row in input_type_rows}

        return AIUsageSummary(
            total_calls=total_calls,
            total_tokens=total_tokens,
            calls_by_provider=calls_by_provider,
            calls_by_input_type=calls_by_input_type,
            period_start=start_date,
            period_end=end_date,
        )

    @staticmethod
    def cleanup_old_logs(db: Session, retention_days: int) -> int:
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        count = (
            db.query(AIUsageLog)
            .filter(AIUsageLog.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        logger.info("Cleaned up old AI usage logs", extra={"deleted_count": count, "retention_days": retention_days})
        return count
