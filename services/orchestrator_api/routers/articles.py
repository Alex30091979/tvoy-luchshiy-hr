"""Articles: GET list, GET by id, POST approve."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from libs.common.database import session_scope
from libs.common.models.db_models import Article, ArticleStatus
from libs.common.schemas.articles import ArticleApproveRequest, ArticleListResponse, ArticleResponse

router = APIRouter()


@router.get("", response_model=ArticleListResponse)
def list_articles(
    status: str | None = Query(None),
    cluster_id: int | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
) -> ArticleListResponse:
    with session_scope() as session:
        q = select(Article).options(joinedload(Article.cluster)).order_by(Article.created_at.desc())
        count_q = select(func.count(Article.id))
        if status:
            q = q.where(Article.status == status)
            count_q = count_q.where(Article.status == status)
        if cluster_id is not None:
            q = q.where(Article.cluster_id == cluster_id)
            count_q = count_q.where(Article.cluster_id == cluster_id)
        total = session.execute(count_q).scalars().one()
        rows = session.execute(q.offset(offset).limit(limit)).unique().scalars().all()
        items = [ArticleResponse.model_validate(r) for r in rows]
        return ArticleListResponse(items=items, total=total)


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int) -> ArticleResponse:
    with session_scope() as session:
        row = session.execute(select(Article).options(joinedload(Article.cluster)).where(Article.id == article_id)).unique().scalars().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        return ArticleResponse.model_validate(row)


@router.post("/{article_id}/approve", response_model=ArticleResponse)
def approve_article(article_id: int, body: ArticleApproveRequest) -> ArticleResponse:
    with session_scope() as session:
        row = session.execute(select(Article).where(Article.id == article_id)).scalars().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        if row.status not in (ArticleStatus.DRAFT.value, ArticleStatus.PENDING_APPROVAL.value):
            raise HTTPException(status_code=400, detail=f"Cannot approve article in status {row.status}")
        row.status = ArticleStatus.PUBLISHED.value if body.publish else ArticleStatus.APPROVED.value
        session.flush()
        session.refresh(row)
        return ArticleResponse.model_validate(row)
