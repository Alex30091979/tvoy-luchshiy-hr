"""Publisher Tilda: draft/publish via API (interface + stub)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from pydantic import BaseModel
from libs.common.clients.tilda import TildaStubClient, TildaPublishRequest

app = FastAPI(title="Publisher Tilda")


class PublishRequest(BaseModel):
    title: str
    slug: str
    html_or_markdown: str
    meta_title: str | None = None
    meta_description: str | None = None
    as_draft: bool = True


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "publisher-tilda"}


@app.post("/publish")
def publish(body: PublishRequest) -> dict:
    req = TildaPublishRequest(
        title=body.title,
        slug=body.slug,
        html_or_markdown=body.html_or_markdown,
        meta_title=body.meta_title,
        meta_description=body.meta_description,
        as_draft=body.as_draft,
    )
    res = TildaStubClient().publish(req)
    return {"page_id": res.page_id, "url": res.url, "is_draft": res.is_draft}
