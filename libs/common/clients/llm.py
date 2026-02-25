"""LLM client abstraction for content generation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class GenerationBrief(BaseModel):
    topic: str
    target_keyword: str
    region: str
    suggested_structure: dict[str, Any]
    intent_summary: str
    max_tokens: int = 2000


class LLMClientInterface(ABC):
    @abstractmethod
    def generate_article_draft(self, brief: GenerationBrief) -> str:
        """Generate original draft markdown from brief. No copying."""
        ...


class LLMStubClient(LLMClientInterface):
    """Stub: returns placeholder markdown without API key."""

    def generate_article_draft(self, brief: GenerationBrief) -> str:
        return f"""# {brief.topic}

*Оригинальный материал. Ключевое слово: {brief.target_keyword}. Регион: {brief.region}.*

## Введение

Краткое введение по теме (генерируется LLM в продакшене).

## Основной раздел

Содержание на основе структуры: {brief.suggested_structure}.

## Заключение

Итоги и призыв к действию.

---
*Сгенерировано SEO AI Agent (stub).*
"""
