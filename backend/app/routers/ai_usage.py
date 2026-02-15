import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.ai_usage import AIUsageLogList, AIUsageSummary
from app.services.ai_usage_service import AIUsageService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/logs", response_model=AIUsageLogList)
async def get_usage_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[UUID] = Query(None),
    provider: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AIUsageLogList:
    """Get paginated AI usage logs. Admin only."""
    return AIUsageService.get_usage_logs(
        db,
        page=page,
        page_size=page_size,
        user_id=user_id,
        provider=provider,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/summary", response_model=AIUsageSummary)
async def get_usage_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AIUsageSummary:
    """Get aggregated AI usage statistics. Admin only."""
    return AIUsageService.get_usage_summary(
        db, start_date=start_date, end_date=end_date
    )


@router.delete("/logs")
async def delete_usage_logs(
    retention_days: int = Query(..., ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete AI usage logs older than retention_days. Admin only."""
    deleted = AIUsageService.cleanup_old_logs(db, retention_days)
    logger.info(
        "Manual AI usage log cleanup",
        extra={"deleted_count": deleted, "retention_days": retention_days, "admin_user": str(current_user.id)},
    )
    return {"deleted": deleted}
