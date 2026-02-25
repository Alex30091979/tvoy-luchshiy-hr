"""Uniqueness/anti-plagiarism check interface."""
from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class UniquenessResult(BaseModel):
    score: float  # 0..1, 1 = unique
    pass_: bool
    details: str | None = None


class AntiPlagiatInterface(ABC):
    @abstractmethod
    def check(self, text: str) -> UniquenessResult:
        """Check text uniqueness. No copying from other sources."""
        ...


class AntiPlagiatStubClient(AntiPlagiatInterface):
    """Stub: always returns pass for MVP."""

    def check(self, text: str) -> UniquenessResult:
        return UniquenessResult(score=1.0, pass_=True, details="Stub: no real check")
