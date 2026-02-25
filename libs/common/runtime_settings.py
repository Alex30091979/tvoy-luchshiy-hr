"""Runtime settings from DB (override env). Used by pipeline so admin changes apply without restart."""
from __future__ import annotations

from sqlalchemy import select

from libs.common.database import session_scope
from libs.common.models.db_models import Setting


def get_setting_from_db(key: str) -> str | None:
    """Return value for key from settings table, or None if not set."""
    with session_scope() as session:
        row = session.execute(select(Setting).where(Setting.key == key)).scalars().one_or_none()
        return row.value if row else None


def get_publish_mode() -> str:
    """Publish mode: auto | semi. DB overrides env."""
    v = get_setting_from_db("publish_mode")
    if v in ("auto", "semi"):
        return v
    from libs.common.config import get_settings
    return get_settings().publish_mode


def get_moscow_share() -> float:
    """Share of Moscow (0..1). DB overrides env."""
    v = get_setting_from_db("moscow_share")
    if v is not None:
        try:
            return float(v)
        except ValueError:
            pass
    from libs.common.config import get_settings
    return get_settings().moscow_share


def get_articles_per_day() -> int:
    """Max articles per day. DB overrides env."""
    v = get_setting_from_db("articles_per_day")
    if v is not None:
        try:
            return int(v)
        except ValueError:
            pass
    from libs.common.config import get_settings
    return get_settings().articles_per_day
