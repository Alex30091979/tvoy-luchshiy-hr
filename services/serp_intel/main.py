"""SERP Intel: analyze SERP for structure/intent only (stub + interface)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI, Query
from libs.common.clients.serp import SerpStubClient, SerpAnalysis

app = FastAPI(title="SERP Intel")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "serp-intel"}


@app.get("/analyze")
def analyze(query: str = Query(...), region: str = Query("moscow")) -> dict:
    analysis = SerpStubClient().analyze(query, region)
    return {
        "query": analysis.query,
        "region": analysis.region,
        "items": [i.model_dump() for i in analysis.items],
        "intent_summary": analysis.intent_summary,
        "suggested_structure": analysis.suggested_structure,
    }
