"""Add deterministic ingestion retry identity to the existing result table."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260821_0004"
down_revision = "20260821_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("ingested_provider_results")}
    if "ingestion_key" not in columns:
        with op.batch_alter_table("ingested_provider_results") as batch:
            batch.add_column(sa.Column("ingestion_key", sa.String(length=64), nullable=True))
        op.execute("UPDATE ingested_provider_results SET ingestion_key = id WHERE ingestion_key IS NULL")
        with op.batch_alter_table("ingested_provider_results") as batch:
            batch.alter_column("ingestion_key", existing_type=sa.String(length=64), nullable=False)
            batch.create_unique_constraint("uq_ingested_result_request_product", ["search_session_id", "provider", "product_id", "ingestion_key"])


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("ingested_provider_results")}
    if "ingestion_key" in columns:
        with op.batch_alter_table("ingested_provider_results") as batch:
            batch.drop_constraint("uq_ingested_result_request_product", type_="unique")
            batch.drop_column("ingestion_key")
