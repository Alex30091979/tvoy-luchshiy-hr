"""Initial schema: settings, clusters, keywords, articles, jobs, performance, link_sites, link_tasks, case_templates.

Revision ID: 001
Revises:
Create Date: 2025-02-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("description", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_settings_key"), "settings", ["key"], unique=True)

    op.create_table(
        "clusters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("region", sa.String(64), nullable=False),
        sa.Column("slug", sa.String(256), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clusters_slug"), "clusters", ["slug"], unique=True)

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_type", sa.String(32), nullable=False, server_default="daily_run"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rq_job_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_jobs_rq_job_id"), "jobs", ["rq_job_id"], unique=False)
    op.create_index(op.f("ix_jobs_status"), "jobs", ["status"], unique=False)
    op.create_index(op.f("ix_jobs_job_type"), "jobs", ["job_type"], unique=False)

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=True),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("slug", sa.String(512), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("target_keyword", sa.String(256), nullable=True),
        sa.Column("draft_markdown", sa.Text(), nullable=True),
        sa.Column("final_markdown", sa.Text(), nullable=True),
        sa.Column("meta_title", sa.String(256), nullable=True),
        sa.Column("meta_description", sa.String(512), nullable=True),
        sa.Column("faq_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("schema_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tilda_page_id", sa.String(64), nullable=True),
        sa.Column("tilda_url", sa.String(1024), nullable=True),
        sa.Column("index_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality_scores", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_articles_cluster_id"), "articles", ["cluster_id"], unique=False)
    op.create_index(op.f("ix_articles_job_id"), "articles", ["job_id"], unique=False)
    op.create_index(op.f("ix_articles_slug"), "articles", ["slug"], unique=False)
    op.create_index(op.f("ix_articles_status"), "articles", ["status"], unique=False)

    op.create_table(
        "keywords",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("keyword", sa.String(256), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_keywords_cluster_keyword", "keywords", ["cluster_id", "keyword"], unique=True)
    op.create_index(op.f("ix_keywords_cluster_id"), "keywords", ["cluster_id"], unique=False)

    op.create_table(
        "performance",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("position_avg", sa.Numeric(10, 2), nullable=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_performance_article_date_source", "performance", ["article_id", "date", "source"], unique=True)
    op.create_index(op.f("ix_performance_article_id"), "performance", ["article_id"], unique=False)

    op.create_table(
        "link_sites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "link_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=True),
        sa.Column("target_url", sa.String(1024), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["site_id"], ["link_sites.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_link_tasks_article_id"), "link_tasks", ["article_id"], unique=False)
    op.create_index(op.f("ix_link_tasks_site_id"), "link_tasks", ["site_id"], unique=False)

    op.create_table(
        "case_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("slug", sa.String(256), nullable=False),
        sa.Column("fields_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_case_templates_slug"), "case_templates", ["slug"], unique=False)


def downgrade() -> None:
    op.drop_table("case_templates")
    op.drop_index(op.f("ix_link_tasks_site_id"), table_name="link_tasks")
    op.drop_index(op.f("ix_link_tasks_article_id"), table_name="link_tasks")
    op.drop_table("link_tasks")
    op.drop_table("link_sites")
    op.drop_index("ix_performance_article_date_source", table_name="performance")
    op.drop_index(op.f("ix_performance_article_id"), table_name="performance")
    op.drop_table("performance")
    op.drop_index("ix_keywords_cluster_keyword", table_name="keywords")
    op.drop_index(op.f("ix_keywords_cluster_id"), table_name="keywords")
    op.drop_table("keywords")
    op.drop_index(op.f("ix_articles_status"), table_name="articles")
    op.drop_index(op.f("ix_articles_slug"), table_name="articles")
    op.drop_index(op.f("ix_articles_job_id"), table_name="articles")
    op.drop_index(op.f("ix_articles_cluster_id"), table_name="articles")
    op.drop_table("articles")
    op.drop_index(op.f("ix_jobs_job_type"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_status"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_rq_job_id"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_clusters_slug"), table_name="clusters")
    op.drop_table("clusters")
    op.drop_index(op.f("ix_settings_key"), table_name="settings")
    op.drop_table("settings")
