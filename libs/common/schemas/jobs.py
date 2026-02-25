"""Job API schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class JobRunDailyRequest(BaseModel):
    dry_run: bool = False


class JobCreate(BaseModel):
    job_type: str = "daily_run"
    payload: Optional[dict[str, Any]] = None


class JobResponse(BaseModel):
    id: int
    job_type: str
    status: str
    payload: Optional[dict[str, Any]] = None
    result: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    rq_job_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
