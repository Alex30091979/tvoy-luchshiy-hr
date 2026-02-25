"""Clusters CRUD."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from libs.common.database import session_scope
from libs.common.models.db_models import Cluster, Keyword
from libs.common.schemas.clusters import (
    ClusterCreate,
    ClusterResponse,
    ClusterUpdate,
    KeywordCreate,
    KeywordResponse,
)

router = APIRouter()


@router.get("", response_model=list[ClusterResponse])
def list_clusters(
    region: str | None = Query(None, description="moscow | rf"),
    is_active: bool | None = None,
) -> list[ClusterResponse]:
    with session_scope() as session:
        q = select(Cluster).options(joinedload(Cluster.keywords)).order_by(Cluster.priority.desc(), Cluster.id)
        if region:
            q = q.where(Cluster.region == region)
        if is_active is not None:
            q = q.where(Cluster.is_active == is_active)
        rows = session.execute(q).unique().scalars().all()
        return [
            ClusterResponse(
                id=r.id,
                name=r.name,
                region=r.region,
                slug=r.slug,
                is_active=r.is_active,
                priority=r.priority,
                created_at=r.created_at,
                updated_at=r.updated_at,
                keywords=[KeywordResponse.model_validate(k) for k in r.keywords],
            )
            for r in rows
        ]


@router.get("/{cluster_id}", response_model=ClusterResponse)
def get_cluster(cluster_id: int) -> ClusterResponse:
    with session_scope() as session:
        row = session.execute(
            select(Cluster).options(joinedload(Cluster.keywords)).where(Cluster.id == cluster_id)
        ).unique().scalars().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Cluster not found")
        return ClusterResponse(
            id=row.id,
            name=row.name,
            region=row.region,
            slug=row.slug,
            is_active=row.is_active,
            priority=row.priority,
            created_at=row.created_at,
            updated_at=row.updated_at,
            keywords=[KeywordResponse.model_validate(k) for k in row.keywords],
        )


@router.post("", response_model=ClusterResponse, status_code=201)
def create_cluster(body: ClusterCreate) -> ClusterResponse:
    with session_scope() as session:
        cluster = Cluster(
            name=body.name,
            region=body.region,
            slug=body.slug,
            is_active=body.is_active,
            priority=body.priority,
        )
        session.add(cluster)
        session.flush()
        for kw in body.keywords:
            session.add(Keyword(cluster_id=cluster.id, keyword=kw.keyword, volume=kw.volume))
        session.refresh(cluster)
        session.refresh(cluster)
        cluster = session.execute(select(Cluster).options(joinedload(Cluster.keywords)).where(Cluster.id == cluster.id)).unique().scalars().one()
        return ClusterResponse(
            id=cluster.id,
            name=cluster.name,
            region=cluster.region,
            slug=cluster.slug,
            is_active=cluster.is_active,
            priority=cluster.priority,
            created_at=cluster.created_at,
            updated_at=cluster.updated_at,
            keywords=[KeywordResponse.model_validate(k) for k in cluster.keywords],
        )


@router.patch("/{cluster_id}", response_model=ClusterResponse)
def update_cluster(cluster_id: int, body: ClusterUpdate) -> ClusterResponse:
    with session_scope() as session:
        row = session.execute(select(Cluster).options(joinedload(Cluster.keywords)).where(Cluster.id == cluster_id)).unique().scalars().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Cluster not found")
        if body.name is not None:
            row.name = body.name
        if body.region is not None:
            row.region = body.region
        if body.slug is not None:
            row.slug = body.slug
        if body.is_active is not None:
            row.is_active = body.is_active
        if body.priority is not None:
            row.priority = body.priority
        session.flush()
        session.refresh(row)
        return ClusterResponse(
            id=row.id,
            name=row.name,
            region=row.region,
            slug=row.slug,
            is_active=row.is_active,
            priority=row.priority,
            created_at=row.created_at,
            updated_at=row.updated_at,
            keywords=[KeywordResponse.model_validate(k) for k in row.keywords],
        )


@router.delete("/{cluster_id}", status_code=204)
def delete_cluster(cluster_id: int) -> None:
    with session_scope() as session:
        row = session.execute(select(Cluster).where(Cluster.id == cluster_id)).scalars().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Cluster not found")
        session.delete(row)
