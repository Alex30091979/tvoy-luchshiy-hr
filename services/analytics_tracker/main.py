"""Analytics Tracker: impressions/clicks/positions (placeholder)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI

app = FastAPI(title="Analytics Tracker")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "analytics-tracker"}


@app.get("/performance")
def performance() -> dict:
    return {"items": [], "message": "Placeholder: integrate GSC/Yandex later"}
