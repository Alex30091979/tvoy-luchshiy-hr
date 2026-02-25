"""Article API schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ArticleBase(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    status: Optional[str] = None
    target_keyword: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ArticleCreate(ArticleBase):
    cluster_id: Optional[int] = None
    target_keyword: Optional[str] = None


class ArticleResponse(ArticleBase):
    id: int
    cluster_id: Optional[int] = None
    job_id: Optional[int] = None
    status: str
    draft_markdown: Optional[str] = None
    final_markdown: Optional[str] = None
    faq_json: Optional[dict[str, Any]] = None
    schema_json: Optional[dict[str, Any]] = None
    tilda_page_id: Optional[str] = None
    tilda_url: Optional[str] = None
    index_requested_at: Optional[datetime] = None
    quality_scores: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int


class ArticleApproveRequest(BaseModel):
    publish: bool = Field(default=True, description="If true, move to published; else just approve")
