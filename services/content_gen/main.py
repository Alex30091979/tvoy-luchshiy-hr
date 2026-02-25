"""Content Gen: draft markdown from brief via LLM (interface + stub)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from pydantic import BaseModel
from libs.common.clients.llm import LLMStubClient, GenerationBrief

app = FastAPI(title="Content Gen")


class GenerateRequest(BaseModel):
    topic: str
    target_keyword: str
    region: str = "moscow"
    suggested_structure: dict = {}
    intent_summary: str = ""


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "content-gen"}


@app.post("/generate")
def generate(body: GenerateRequest) -> dict:
    brief = GenerationBrief(
        topic=body.topic,
        target_keyword=body.target_keyword,
        region=body.region,
        suggested_structure=body.suggested_structure,
        intent_summary=body.intent_summary,
    )
    draft = LLMStubClient().generate_article_draft(brief)
    return {"draft_markdown": draft}
