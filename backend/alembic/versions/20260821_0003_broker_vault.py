"""Broker-owned encrypted OAuth vault table."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260821_0003"
down_revision = "20260821_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "broker_vault_credentials" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "broker_vault_credentials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subject_ref", sa.String(64), nullable=False, unique=True),
        sa.Column("provider_id", sa.String(80), nullable=False),
        sa.Column("access_token_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("refresh_token_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("key_version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("scopes", sa.String(1000), nullable=False, server_default=""),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_broker_vault_credentials_subject_ref", "broker_vault_credentials", ["subject_ref"], unique=True)
    op.create_index("ix_broker_vault_credentials_provider_id", "broker_vault_credentials", ["provider_id"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'truecost_broker') THEN GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE broker_vault_credentials TO truecost_broker; END IF; END $$")
        op.execute("DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'truecost_api') THEN GRANT USAGE ON SCHEMA public TO truecost_api; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO truecost_api; REVOKE ALL ON TABLE broker_vault_credentials FROM truecost_api; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO truecost_api; END IF; END $$")


def downgrade() -> None:
    op.drop_table("broker_vault_credentials")
