"""Cases Gen: case template with fields for human to fill (no invented facts)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from libs.common.database import session_scope
from libs.common.models.db_models import CaseTemplate

app = FastAPI(title="Cases Gen")


class CaseTemplateCreate(BaseModel):
    title: str
    slug: str
    fields_schema: dict  # e.g. {"company": "string", "result": "string", "challenge": "string"}
    is_active: bool = True


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "cases-gen"}


@app.get("/templates")
def list_templates() -> list:
    with session_scope() as session:
        rows = session.execute(select(CaseTemplate).where(CaseTemplate.is_active == True)).scalars().all()
        return [{"id": r.id, "title": r.title, "slug": r.slug, "fields_schema": r.fields_schema} for r in rows]


@app.post("/templates", status_code=201)
def create_template(body: CaseTemplateCreate) -> dict:
    with session_scope() as session:
        t = CaseTemplate(title=body.title, slug=body.slug, fields_schema=body.fields_schema, is_active=body.is_active)
        session.add(t)
        session.flush()
        session.refresh(t)
        return {"id": t.id, "title": t.title, "slug": t.slug, "fields_schema": t.fields_schema}


@app.post("/generate_draft")
def generate_draft(slug: str = Query(..., description="Template slug")) -> dict:
    """Generate case skeleton from template — fields to fill by human, no fake data."""
    with session_scope() as session:
        row = session.execute(select(CaseTemplate).where(CaseTemplate.slug == slug)).scalars().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Template not found")
        return {
            "title": row.title,
            "slug": row.slug,
            "fields": {k: "" for k in row.fields_schema},
            "instructions": "Заполните поля реальными данными. Не выдумывайте факты.",
        }
