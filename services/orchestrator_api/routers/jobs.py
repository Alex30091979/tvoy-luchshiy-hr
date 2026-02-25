"""Jobs: POST /jobs/run_daily, GET list, GET job status."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func

from libs.common.config import get_settings
from libs.common.database import session_scope
from libs.common.models.db_models import Job, JobStatus, JobType
from libs.common.schemas.jobs import JobListResponse, JobResponse, JobRunDailyRequest

router = APIRouter()


@router.get("", response_model=JobListResponse)
def list_jobs(
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
) -> JobListResponse:
    with session_scope() as session:
        q = select(Job).order_by(Job.created_at.desc())
        count_q = select(func.count(Job.id))
        if status:
            q = q.where(Job.status == status)
            count_q = count_q.where(Job.status == status)
        total = session.execute(count_q).scalars().one()
        rows = session.execute(q.offset(offset).limit(limit)).scalars().all()
        return JobListResponse(items=[JobResponse.model_validate(r) for r in rows], total=total)


def enqueue_daily_run(dry_run: bool = False) -> str | None:
    """Enqueue daily run job in RQ; returns rq_job_id or None if queue unavailable."""
    try:
        from redis import Redis
        from rq import Queue
        from services.scheduler_worker.tasks import run_daily_pipeline
        redis = Redis.from_url(get_settings().redis_url)
        q = Queue("default", connection=redis)
        job = q.enqueue(run_daily_pipeline, dry_run=dry_run, job_timeout="30m")
        return job.id
    except Exception:
        return None


@router.post("/run_daily", response_model=JobResponse)
def run_daily(body: JobRunDailyRequest | None = None) -> JobResponse:
    dry_run = body.dry_run if body else True
    with session_scope() as session:
        job = Job(
            job_type=JobType.DAILY_RUN.value,
            status=JobStatus.PENDING.value,
            payload={"dry_run": dry_run},
        )
        session.add(job)
        session.flush()
        rq_job_id = enqueue_daily_run(dry_run=dry_run)
        if rq_job_id:
            job.rq_job_id = rq_job_id
        session.flush()
        session.refresh(job)
        return JobResponse.model_validate(job)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int) -> JobResponse:
    with session_scope() as session:
        row = session.execute(select(Job).where(Job.id == job_id)).scalars().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobResponse.model_validate(row)
