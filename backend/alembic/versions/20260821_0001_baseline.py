"""TrueCost production baseline schema.

This baseline is intentionally tied to the immutable revision. Later model changes
must use explicit Alembic revisions rather than application startup DDL.
"""
from __future__ import annotations

from alembic import op

revision = "20260821_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The reviewed baseline contains every table registered at this revision.
    # create_all is used only by this migration, never by production startup.
    from app.db import Base
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    from app.db import Base
    import app.models  # noqa: F401
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
