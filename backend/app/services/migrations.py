from __future__ import annotations


def migration_status(database_url: str) -> tuple[bool, str | None, str | None]:
    """Return (current, database_revision, code_head) without mutating schema."""
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from sqlalchemy import create_engine

    import os
    ini_path = "backend/alembic.ini" if os.path.exists("backend/alembic.ini") else "alembic.ini"
    config = Config(ini_path)
    if os.path.exists("backend/alembic"):
        config.set_main_option("script_location", "backend/alembic")
    script = ScriptDirectory.from_config(config)
    head = script.get_current_head()
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            current = MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()
    return current == head, current, head
