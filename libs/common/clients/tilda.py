"""Tilda publisher interface — draft/publish."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class TildaPublishRequest(BaseModel):
    title: str
    slug: str
    html_or_markdown: str
    meta_title: str | None = None
    meta_description: str | None = None
    as_draft: bool = True


class TildaPublishResult(BaseModel):
    page_id: str
    url: str
    is_draft: bool


class TildaPublisherInterface(ABC):
    @abstractmethod
    def publish(self, request: TildaPublishRequest) -> TildaPublishResult:
        """Create/update page. as_draft=True => draft, False => publish."""
        ...


class TildaStubClient(TildaPublisherInterface):
    """Stub: no real Tilda API call."""

    def publish(self, request: TildaPublishRequest) -> TildaPublishResult:
        return TildaPublishResult(
            page_id="stub-page-001",
            url=f"https://tilda.cc/stub/{request.slug}",
            is_draft=request.as_draft,
        )
