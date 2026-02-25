"""Quality Gate: spam/keyword stuffing/length; uniqueness (interface + stub)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from pydantic import BaseModel
from libs.common.clients.antiplagiat import AntiPlagiatStubClient

app = FastAPI(title="Quality Gate")


class CheckRequest(BaseModel):
    text: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "quality-gate"}


@app.post("/check")
def check(body: CheckRequest) -> dict:
    result = AntiPlagiatStubClient().check(body.text)
    length_ok = 500 <= len(body.text) <= 50000
    return {
        "pass": result.pass_ and length_ok,
        "uniqueness": result.score,
        "keyword_stuffing": False,
        "length_ok": length_ok,
        "details": result.details or "stub",
    }
