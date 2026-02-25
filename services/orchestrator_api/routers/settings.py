"""Settings CRUD — GET/POST."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from libs.common.database import session_scope
from libs.common.models.db_models import Setting
from libs.common.schemas.settings import SettingItem, SettingUpdate

router = APIRouter()


@router.get("", response_model=list[SettingItem])
def list_settings() -> list[SettingItem]:
    with session_scope() as session:
        rows = session.execute(select(Setting)).scalars().all()
        return [SettingItem(key=r.key, value=r.value, description=r.description) for r in rows]


@router.get("/{key}", response_model=SettingItem)
def get_setting(key: str) -> SettingItem:
    with session_scope() as session:
        row = session.execute(select(Setting).where(Setting.key == key)).scalars().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Setting not found")
        return SettingItem(key=row.key, value=row.value, description=row.description)


@router.post("", response_model=SettingItem)
def create_or_update_setting(item: SettingItem) -> SettingItem:
    with session_scope() as session:
        row = session.execute(select(Setting).where(Setting.key == item.key)).scalars().one_or_none()
        if row:
            row.value = item.value
            row.description = item.description
        else:
            row = Setting(key=item.key, value=item.value, description=item.description)
            session.add(row)
        session.flush()
        session.refresh(row)
        return SettingItem(key=row.key, value=row.value, description=row.description)


@router.patch("/{key}", response_model=SettingItem)
def update_setting(key: str, body: SettingUpdate) -> SettingItem:
    with session_scope() as session:
        row = session.execute(select(Setting).where(Setting.key == key)).scalars().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Setting not found")
        if body.value is not None:
            row.value = body.value
        if body.description is not None:
            row.description = body.description
        session.flush()
        session.refresh(row)
        return SettingItem(key=row.key, value=row.value, description=row.description)
