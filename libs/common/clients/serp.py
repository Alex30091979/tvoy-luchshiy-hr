"""SERP provider abstraction — structure/intent only, no content copy."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class SerpResultItem(BaseModel):
    title: str
    url: str
    snippet: str
    position: int
    structure_hint: str | None = None  # e.g. "list", "how-to", "faq"


class SerpAnalysis(BaseModel):
    query: str
    region: str
    items: list[SerpResultItem]
    intent_summary: str
    suggested_structure: dict[str, Any]  # headings, sections suggested by SERP


class SerpProviderInterface(ABC):
    @abstractmethod
    def analyze(self, query: str, region: str = "moscow") -> SerpAnalysis:
        """Analyze SERP for structure and intent only. No content copying."""
        ...


class SerpStubClient(SerpProviderInterface):
    """Stub: returns fake structure for MVP without API keys."""

    def analyze(self, query: str, region: str = "moscow") -> SerpAnalysis:
        return SerpAnalysis(
            query=query,
            region=region,
            items=[
                SerpResultItem(title=f"Example {query}", url="https://example.com/1", snippet="...", position=1, structure_hint="article"),
                SerpResultItem(title=f"Guide {query}", url="https://example.com/2", snippet="...", position=2, structure_hint="how-to"),
            ],
            intent_summary="Informational: user seeks guidance on the topic.",
            suggested_structure={
                "h1": query,
                "sections": ["intro", "benefits", "how_to_choose", "faq"],
            },
        )
