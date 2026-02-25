"""SEO Optimizer: semantics, LSI, meta, FAQ, schema_json (stub)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SEO Optimizer")


class OptimizeRequest(BaseModel):
    draft_markdown: str
    target_keyword: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "seo-optimizer"}


@app.post("/optimize")
def optimize(body: OptimizeRequest) -> dict:
    return {
        "final_markdown": body.draft_markdown,
        "meta_title": body.target_keyword[:60],
        "meta_description": (body.target_keyword + " — материал для B2B.")[:160],
        "faq_json": None,
        "schema_json": {"@type": "Article"},
    }
