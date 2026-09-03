from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.config import settings
from app.db import engine

router = APIRouter()


@router.get("/live")
def live() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict:
    checks: dict[str, object] = {"database": False, "redis": settings.task_execution_mode != "celery", "migration": False, "workers": settings.task_execution_mode}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = True
        from app.services.migrations import migration_status
        current, revision, head = migration_status(settings.database_url)
        checks.update({"migration": current, "database_revision": revision, "migration_head": head})
        if settings.task_execution_mode == "celery":
            from redis import Redis
            checks["redis"] = bool(Redis.from_url(settings.redis_url).ping())
    except Exception as exc:
        checks["error"] = type(exc).__name__
    if not checks["database"] or not checks["redis"] or not checks["migration"]:
        raise HTTPException(status_code=503, detail={"code": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}
