from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class AIUsageLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    provider: str
    model: str
    input_type: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    success: bool
    error_message: Optional[str]
    duration_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class AIUsageLogList(BaseModel):
    items: List[AIUsageLogResponse]
    total: int
    page: int
    page_size: int


class AIUsageSummary(BaseModel):
    total_calls: int
    total_tokens: int
    calls_by_provider: Dict[str, int]
    calls_by_input_type: Dict[str, int]
    period_start: Optional[datetime]
    period_end: Optional[datetime]
