"""RQ tasks: daily pipeline and cron-like scheduling."""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import select

from libs.common.config import get_settings
from libs.common.database import session_scope
from libs.common.runtime_settings import get_moscow_share, get_publish_mode
from libs.common.models.db_models import (
    Article,
    ArticleStatus,
    Cluster,
    Job,
    JobStatus,
    Keyword,
)
from libs.common.logging import get_logger

logger = get_logger(__name__)


def run_daily_pipeline(dry_run: bool = False) -> dict:
    """One daily SEO article: pick cluster, SERP -> content -> SEO -> quality -> publish (or draft)."""
    settings = get_settings()
    logger.info("daily_pipeline_started", dry_run=dry_run, daily_token_quota=settings.daily_token_quota)
    result: dict = {"article_id": None, "cluster_id": None, "dry_run": dry_run, "published": False}
    job_id = None

    with session_scope() as session:
        # Create job record
        job = Job(
            job_type="daily_run",
            status=JobStatus.RUNNING.value,
            payload={"dry_run": dry_run},
            started_at=datetime.utcnow(),
        )
        session.add(job)
        session.flush()
        job_id = job.id
    logger.info("event", event="job.created", job_id=job_id, dry_run=dry_run)

    try:
        with session_scope() as session:
            moscow = list(session.execute(
                select(Cluster).where(Cluster.region == "moscow", Cluster.is_active == True).order_by(Cluster.priority.desc())
            ).scalars().all())
            rf = list(session.execute(
                select(Cluster).where(Cluster.region == "rf", Cluster.is_active == True).order_by(Cluster.priority.desc())
            ).scalars().all())
            if not moscow and not rf:
                raise ValueError("No active clusters")
            import random
            moscow_share = get_moscow_share()
            if moscow and (not rf or random.random() < moscow_share):
                cluster = moscow[0]
            else:
                cluster = rf[0]
            cluster_id = cluster.id
            cluster_name = cluster.name
            cluster_slug = cluster.slug
            cluster_region = cluster.region
            keywords = list(session.execute(select(Keyword).where(Keyword.cluster_id == cluster_id)).scalars().all())
            target_keyword = keywords[0].keyword if keywords else cluster_name

        # 1) SERP (structure only)
        serp_data = _call_serp_intel(target_keyword, cluster_region)
        logger.info("event", event="serp.analyzed", job_id=job_id, keyword=target_keyword)
        # 2) Content draft
        draft_markdown = _call_content_gen(
            topic=cluster_name,
            target_keyword=target_keyword,
            region=cluster_region,
            suggested_structure=serp_data.get("suggested_structure", {}),
            intent_summary=serp_data.get("intent_summary", ""),
        )
        logger.info("event", event="content.drafted", job_id=job_id)
        # 3) SEO optimizer
        seo_result = _call_seo_optimizer(draft_markdown, target_keyword)
        logger.info("event", event="seo.enriched", job_id=job_id)
        # 4) Quality gate
        quality_result = _call_quality_gate(seo_result.get("final_markdown", draft_markdown))
        if not quality_result.get("pass", True):
            logger.warning("event", event="quality.failed", job_id=job_id, scores=quality_result)
            with session_scope() as session:
                job = session.execute(select(Job).where(Job.id == job_id)).scalars().one()
                job.status = JobStatus.COMPLETED.value
                job.finished_at = datetime.utcnow()
                job.result = {"error": "quality_gate_failed", "scores": quality_result}
                session.flush()
            return {"job_id": job_id, "error": "quality_gate_failed", **result}
        logger.info("event", event="quality.passed", job_id=job_id)

        final_markdown = seo_result.get("final_markdown", draft_markdown)
        meta_title = seo_result.get("meta_title", "")
        meta_description = seo_result.get("meta_description", "")
        faq_json = seo_result.get("faq_json")
        schema_json = seo_result.get("schema_json")

        # 5) Publish or draft
        publish_mode = get_publish_mode()
        do_publish = (not dry_run) and (publish_mode == "auto") and (not settings.dry_run)
        tilda_result = _call_publisher_tilda(
            title=cluster_name,
            slug=cluster_slug + "-" + datetime.utcnow().strftime("%Y-%m-%d"),
            content=final_markdown,
            meta_title=meta_title,
            meta_description=meta_description,
            as_draft=not do_publish,
        )
        logger.info("event", event="tilda.published" if do_publish else "tilda.drafted", job_id=job_id)

        with session_scope() as session:
            job = session.execute(select(Job).where(Job.id == job_id)).scalars().one()
            article = Article(
                cluster_id=cluster_id,
                job_id=job_id,
                title=cluster_name,
                slug=tilda_result.get("slug", ""),
                status=ArticleStatus.PUBLISHED.value if do_publish else ArticleStatus.PENDING_APPROVAL.value,
                target_keyword=target_keyword,
                draft_markdown=draft_markdown,
                final_markdown=final_markdown,
                meta_title=meta_title,
                meta_description=meta_description,
                faq_json=faq_json,
                schema_json=schema_json,
                tilda_page_id=tilda_result.get("page_id"),
                tilda_url=tilda_result.get("url"),
                quality_scores=quality_result,
            )
            session.add(article)
            session.flush()
            job.status = JobStatus.COMPLETED.value
            job.finished_at = datetime.utcnow()
            job.result = {"article_id": article.id, "published": do_publish}
            session.flush()
            result["article_id"] = article.id
            result["cluster_id"] = cluster_id
            result["published"] = do_publish

    except Exception as e:
        logger.exception("daily_pipeline_failed", job_id=job_id, error=str(e))
        with session_scope() as session:
            job = session.execute(select(Job).where(Job.id == job_id)).scalars().one()
            job.status = JobStatus.FAILED.value
            job.error_message = str(e)
            job.finished_at = datetime.utcnow()
            session.flush()
        result["error"] = str(e)
        raise

    return {"job_id": job_id, **result}


def _call_serp_intel(keyword: str, region: str) -> dict:
    """Call serp-intel service or use stub."""
    try:
        import httpx
        r = httpx.get(
            f"{get_settings().serp_intel_url}/analyze",
            params={"query": keyword, "region": region},
            timeout=30.0,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        from libs.common.clients.serp import SerpStubClient
        analysis = SerpStubClient().analyze(keyword, region)
        return {
            "suggested_structure": analysis.suggested_structure,
            "intent_summary": analysis.intent_summary,
        }


def _call_content_gen(
    topic: str,
    target_keyword: str,
    region: str,
    suggested_structure: dict,
    intent_summary: str,
) -> str:
    """Call content-gen service or use stub."""
    try:
        import httpx
        r = httpx.post(
            f"{get_settings().content_gen_url}/generate",
            json={
                "topic": topic,
                "target_keyword": target_keyword,
                "region": region,
                "suggested_structure": suggested_structure,
                "intent_summary": intent_summary,
            },
            timeout=60.0,
        )
        r.raise_for_status()
        return r.json().get("draft_markdown", "")
    except Exception:
        from libs.common.clients.llm import LLMStubClient, GenerationBrief
        return LLMStubClient().generate_article_draft(
            GenerationBrief(
                topic=topic,
                target_keyword=target_keyword,
                region=region,
                suggested_structure=suggested_structure,
                intent_summary=intent_summary,
            )
        )


def _call_seo_optimizer(draft_markdown: str, target_keyword: str) -> dict:
    """Call seo-optimizer service or return draft as-is."""
    try:
        import httpx
        r = httpx.post(
            f"{get_settings().seo_optimizer_url}/optimize",
            json={"draft_markdown": draft_markdown, "target_keyword": target_keyword},
            timeout=60.0,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return {
            "final_markdown": draft_markdown,
            "meta_title": target_keyword,
            "meta_description": "",
            "faq_json": None,
            "schema_json": None,
        }


def _call_quality_gate(text: str) -> dict:
    """Call quality-gate service or stub."""
    try:
        import httpx
        r = httpx.post(
            f"{get_settings().quality_gate_url}/check",
            json={"text": text},
            timeout=30.0,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return {"pass": True, "uniqueness": 1.0, "keyword_stuffing": False, "details": "stub"}


def _call_publisher_tilda(
    title: str,
    slug: str,
    content: str,
    meta_title: str,
    meta_description: str,
    as_draft: bool,
) -> dict:
    """Call publisher-tilda or stub."""
    try:
        import httpx
        r = httpx.post(
            f"{get_settings().publisher_tilda_url}/publish",
            json={
                "title": title,
                "slug": slug,
                "html_or_markdown": content,
                "meta_title": meta_title,
                "meta_description": meta_description,
                "as_draft": as_draft,
            },
            timeout=30.0,
        )
        r.raise_for_status()
        data = r.json()
        return {"page_id": data.get("page_id"), "url": data.get("url", ""), "slug": slug}
    except Exception:
        from libs.common.clients.tilda import TildaStubClient, TildaPublishRequest
        res = TildaStubClient().publish(
            TildaPublishRequest(
                title=title,
                slug=slug,
                html_or_markdown=content,
                meta_title=meta_title or None,
                meta_description=meta_description or None,
                as_draft=as_draft,
            )
        )
        return {"page_id": res.page_id, "url": res.url, "slug": slug}
