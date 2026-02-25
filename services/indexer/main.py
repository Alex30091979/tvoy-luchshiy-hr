"""Indexer: GSC / Yandex indexing (interfaces + mocks)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from pydantic import BaseModel
from libs.common.clients.indexer import IndexerStubClient, IndexRequest

app = FastAPI(title="Indexer")


class IndexRequestBody(BaseModel):
    url: str
    source: str = "gsc"  # gsc | yandex


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "indexer"}


@app.post("/request_indexing")
def request_indexing(body: IndexRequestBody) -> dict:
    res = IndexerStubClient().request_indexing(IndexRequest(url=body.url, source=body.source))
    return {"requested": res.requested, "source": res.source, "message": res.message}
