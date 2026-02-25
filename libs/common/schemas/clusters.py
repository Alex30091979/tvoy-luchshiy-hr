"""Cluster and keyword API schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KeywordCreate(BaseModel):
    keyword: str
    volume: Optional[int] = None


class KeywordResponse(BaseModel):
    id: int
    cluster_id: int
    keyword: str
    volume: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ClusterBase(BaseModel):
    name: str
    region: str = Field(..., description="moscow | rf")
    slug: str
    is_active: bool = True
    priority: int = 0


class ClusterCreate(ClusterBase):
    keywords: list[KeywordCreate] = Field(default_factory=list)


class ClusterUpdate(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    slug: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class ClusterResponse(ClusterBase):
    id: int
    created_at: datetime
    updated_at: datetime
    keywords: list[KeywordResponse] = Field(default_factory=list)
    model_config = {"from_attributes": True}
