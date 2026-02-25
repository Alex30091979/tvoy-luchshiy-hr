"""Orchestrator API: settings, clusters, articles, jobs, admin."""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from libs.common.config import get_settings
from libs.common.logging import get_logger
from services.orchestrator_api.routers import health, settings, clusters, articles, jobs

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        from libs.common.logging_config import setup_logging
        setup_logging(json_logs=get_settings().log_json)
    except Exception:
        pass
    logger.info("orchestrator_api_started")
    yield
    logger.info("orchestrator_api_stopped")


app = FastAPI(title="SEO AI Agent — Orchestrator", lifespan=lifespan)

# Mount static and templates if present
admin_dir = Path(__file__).parent / "admin"
if admin_dir.exists():
    app.mount("/static", StaticFiles(directory=admin_dir / "static"), name="static")
templates = Jinja2Templates(directory=str(admin_dir / "templates")) if (admin_dir / "templates").exists() else None

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])
app.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
app.include_router(articles.router, prefix="/articles", tags=["articles"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])


@app.get("/", response_class=HTMLResponse)
async def admin_index(request: Request) -> HTMLResponse:
    """Home: link to admin and API."""
    if templates is None:
        return HTMLResponse(
            "<h1>SEO AI Agent</h1><p><a href='/admin'>Админ</a> | <a href='/docs'>API Docs</a> | <a href='/health'>Health</a></p>"
        )
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_terminal(request: Request) -> HTMLResponse:
    """Admin terminal: AUTO/SEMI, limits, clusters, queue, articles, quality report."""
    if templates is None:
        return HTMLResponse("<h1>Admin</h1><p>Add admin/templates/admin.html</p>")
    return templates.TemplateResponse("admin.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.orchestrator_api.main:app", host="0.0.0.0", port=8000, reload=True)
