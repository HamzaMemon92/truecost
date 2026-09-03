"""Provider operations and administrative role compatibility revision."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260821_0002"
down_revision = "20260821_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_admin" not in user_columns:
        with op.batch_alter_table("users") as batch:
            batch.add_column(sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()))
    connection_columns = {column["name"] for column in inspector.get_columns("provider_connections")}
    if "broker_subject_ref" not in connection_columns:
        with op.batch_alter_table("provider_connections") as batch:
            batch.add_column(sa.Column("broker_subject_ref", sa.String(length=64), nullable=True))
            batch.create_unique_constraint("uq_provider_connections_broker_subject_ref", ["broker_subject_ref"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_admin" in user_columns:
        with op.batch_alter_table("users") as batch:
            batch.drop_column("is_admin")
    connection_columns = {column["name"] for column in inspector.get_columns("provider_connections")}
    if "broker_subject_ref" in connection_columns:
        with op.batch_alter_table("provider_connections") as batch:
            batch.drop_constraint("uq_provider_connections_broker_subject_ref", type_="unique")
            batch.drop_column("broker_subject_ref")
