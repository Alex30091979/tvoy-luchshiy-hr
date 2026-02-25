"""Indexer interface for GSC / Yandex (request indexing)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class IndexRequest(BaseModel):
    url: str
    source: str  # gsc | yandex


class IndexResult(BaseModel):
    requested: bool
    source: str
    message: str | None = None


class IndexerInterface(ABC):
    @abstractmethod
    def request_indexing(self, request: IndexRequest) -> IndexResult:
        """Request URL to be indexed (GSC/Яндекс API or stub)."""
        ...


class IndexerStubClient(IndexerInterface):
    """Stub: just records that indexing was requested."""

    def request_indexing(self, request: IndexRequest) -> IndexResult:
        return IndexResult(requested=True, source=request.source, message="Stub: index requested")
