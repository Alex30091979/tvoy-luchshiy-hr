"""Linkbuilding: link_sites + link_tasks CRUD (uses DB)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from libs.common.database import session_scope
from libs.common.models.db_models import LinkSite, LinkTask

app = FastAPI(title="Linkbuilding")


class LinkSiteCreate(BaseModel):
    name: str
    url: str
    is_active: bool = True


class LinkTaskCreate(BaseModel):
    site_id: int
    article_id: int | None = None
    target_url: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "linkbuilding"}


@app.get("/sites")
def list_sites() -> list:
    with session_scope() as session:
        rows = session.execute(select(LinkSite)).scalars().all()
        return [{"id": r.id, "name": r.name, "url": r.url, "is_active": r.is_active} for r in rows]


@app.post("/sites", status_code=201)
def create_site(body: LinkSiteCreate) -> dict:
    with session_scope() as session:
        site = LinkSite(name=body.name, url=body.url, is_active=body.is_active)
        session.add(site)
        session.flush()
        session.refresh(site)
        return {"id": site.id, "name": site.name, "url": site.url, "is_active": site.is_active}


@app.get("/tasks")
def list_tasks() -> list:
    with session_scope() as session:
        rows = session.execute(select(LinkTask)).scalars().all()
        return [{"id": r.id, "site_id": r.site_id, "article_id": r.article_id, "target_url": r.target_url, "status": r.status} for r in rows]


@app.post("/tasks", status_code=201)
def create_task(body: LinkTaskCreate) -> dict:
    with session_scope() as session:
        task = LinkTask(site_id=body.site_id, article_id=body.article_id, target_url=body.target_url, status="pending")
        session.add(task)
        session.flush()
        session.refresh(task)
        return {"id": task.id, "site_id": task.site_id, "article_id": task.article_id, "status": task.status}
