"""SQLAlchemy ORM models for SEO Agent."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
import enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.common.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


# --- Enums (article & job state machine) ---
class ArticleStatus(str, enum.Enum):
    DRAFT = "draft"           # черновик
    PENDING_APPROVAL = "pending_approval"  # на утверждении
    APPROVED = "approved"     # утверждён
    PUBLISHED = "published"   # опубликован
    REJECTED = "rejected"     # отклонён
    ARCHIVED = "archived"     # в архиве


class JobStatus(str, enum.Enum):
    PENDING = "pending"       # в очереди
    RUNNING = "running"       # выполняется
    COMPLETED = "completed"   # завершён успешно
    FAILED = "failed"         # ошибка
    CANCELLED = "cancelled"   # отменён


class JobType(str, enum.Enum):
    DAILY_RUN = "daily_run"   # ежедневный пайплайн
    SINGLE_ARTICLE = "single_article"
    UPDATE_ARTICLE = "update_article"  # для Update Engine (зарезервировано)


# --- Settings (key-value from DB) ---
class Setting(Base, TimestampMixin):
    __tablename__ = "settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)


# --- Clusters & Keywords ---
class Cluster(Base, TimestampMixin):
    __tablename__ = "clusters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    region: Mapped[str] = mapped_column(String(64), nullable=False)  # moscow | rf
    slug: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # higher = first
    keywords: Mapped[list["Keyword"]] = relationship("Keyword", back_populates="cluster", cascade="all, delete-orphan")
    articles: Mapped[list["Article"]] = relationship("Article", back_populates="cluster")


class Keyword(Base, TimestampMixin):
    __tablename__ = "keywords"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword: Mapped[str] = mapped_column(String(256), nullable=False)
    volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="keywords")
    __table_args__ = (Index("ix_keywords_cluster_keyword", "cluster_id", "keyword", unique=True),)


# --- Articles ---
class Article(Base, TimestampMixin):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True)
    job_id: Mapped[Optional[int]] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    slug: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(32), default=ArticleStatus.DRAFT.value, nullable=False, index=True
    )
    target_keyword: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    draft_markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    final_markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_title: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    faq_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    schema_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tilda_page_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tilda_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    index_requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    quality_scores: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # pass/fail + scores
    cluster: Mapped[Optional["Cluster"]] = relationship("Cluster", back_populates="articles")
    job: Mapped[Optional["Job"]] = relationship("Job", back_populates="articles")


# --- Jobs (queue / pipeline) ---
class Job(Base, TimestampMixin):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(32), default=JobType.DAILY_RUN.value, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default=JobStatus.PENDING.value, nullable=False, index=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # cluster_id, article_id, etc.
    result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rq_job_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    articles: Mapped[list["Article"]] = relationship("Article", back_populates="job")


# --- Performance (analytics placeholder) ---
class Performance(Base, TimestampMixin):
    __tablename__ = "performance"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[Optional[int]] = mapped_column(ForeignKey("articles.id", ondelete="SET NULL"), nullable=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    position_avg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # gsc | yandex
    __table_args__ = (Index("ix_performance_article_date_source", "article_id", "date", "source", unique=True),)


# --- Linkbuilding ---
class LinkSite(Base, TimestampMixin):
    __tablename__ = "link_sites"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tasks: Mapped[list["LinkTask"]] = relationship("LinkTask", back_populates="site", cascade="all, delete-orphan")


class LinkTask(Base, TimestampMixin):
    __tablename__ = "link_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("link_sites.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id: Mapped[Optional[int]] = mapped_column(ForeignKey("articles.id", ondelete="SET NULL"), nullable=True, index=True)
    target_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    site: Mapped["LinkSite"] = relationship("LinkSite", back_populates="tasks")


# --- Case templates (cases-gen) ---
class CaseTemplate(Base, TimestampMixin):
    __tablename__ = "case_templates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    slug: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    fields_schema: Mapped[dict] = mapped_column(JSONB, nullable=False)  # каркас полей для заполнения человеком
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
