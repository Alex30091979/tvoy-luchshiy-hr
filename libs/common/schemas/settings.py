"""Settings API schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SettingItem(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None


class SettingUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
