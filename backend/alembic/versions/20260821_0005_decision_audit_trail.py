"""Persist exact-discovery decision audit artifacts."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260821_0005"
down_revision = "20260821_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "decision_audit_trail" in inspector.get_table_names():
        return
    op.create_table(
        "decision_audit_trail",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("search_session_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("artifact_type", sa.String(length=60), nullable=False),
        sa.Column("artifact_hash", sa.String(length=64), nullable=False),
        sa.Column("selected_identity", sa.JSON(), nullable=False),
        sa.Column("provider_attempts", sa.JSON(), nullable=False),
        sa.Column("exact_results", sa.JSON(), nullable=False),
        sa.Column("related_results", sa.JSON(), nullable=False),
        sa.Column("rejected_results", sa.JSON(), nullable=False),
        sa.Column("final_decision", sa.JSON(), nullable=False),
        sa.Column("freshness", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["search_session_id"], ["search_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("search_session_id", "artifact_type", "artifact_hash", name="uq_decision_audit_artifact"),
    )
    op.create_index(op.f("ix_decision_audit_trail_search_session_id"), "decision_audit_trail", ["search_session_id"], unique=False)
    op.create_index(op.f("ix_decision_audit_trail_user_id"), "decision_audit_trail", ["user_id"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "decision_audit_trail" not in inspector.get_table_names():
        return
    op.drop_index(op.f("ix_decision_audit_trail_user_id"), table_name="decision_audit_trail")
    op.drop_index(op.f("ix_decision_audit_trail_search_session_id"), table_name="decision_audit_trail")
    op.drop_table("decision_audit_trail")
