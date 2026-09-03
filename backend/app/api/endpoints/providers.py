from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.category_catalog import CATALOG
from app.db import get_db
from app.models import IngestedProviderResult, ProviderOperationalState

router = APIRouter()


@router.get("")
def list_providers(db: Session = Depends(get_db)) -> dict:
    """Public capability catalog. Listed providers are not implicitly live."""
    operations = {
        row.provider_id: row
        for row in db.scalars(select(ProviderOperationalState)).all()
    }
    now = datetime.now(timezone.utc)
    categories = [category.model_dump() for category in CATALOG.categories]
    providers: list[dict] = []
    for provider in CATALOG.providers:
        operation = operations.get(provider.id)
        rollout_state = operation.rollout_state if operation else provider.rollout_state
        connection_state = operation.connection_state if operation else provider.account_connection_state
        last_ingested_at = operation.last_ingested_at if operation else None
        stale = bool(
            last_ingested_at
            and (now - (last_ingested_at if last_ingested_at.tzinfo else last_ingested_at.replace(tzinfo=timezone.utc))).total_seconds()
            > provider.freshness_sla_seconds
        )
        providers.append({
            **provider.model_dump(),
            "rollout_state": "degraded" if stale and rollout_state == "verified" else rollout_state,
            "account_connection_state": connection_state,
            "connection_available": connection_state == "enabled",
            "live": rollout_state == "verified" and not stale,
            "last_verified_at": operation.last_verified_at if operation else None,
            "last_ingested_at": last_ingested_at,
        })
    return {"version": CATALOG.version, "categories": categories, "providers": providers}


@router.get("/health")
def provider_health(db: Session = Depends(get_db)) -> dict:
    """Public provider reliability summary. This never marks previews as live."""
    operations = {row.provider_id: row for row in db.scalars(select(ProviderOperationalState)).all()}
    counts = dict(db.execute(select(IngestedProviderResult.provider, func.count(IngestedProviderResult.id)).group_by(IngestedProviderResult.provider)).all())
    latest = dict(db.execute(select(IngestedProviderResult.provider, func.max(IngestedProviderResult.observed_at)).group_by(IngestedProviderResult.provider)).all())
    now = datetime.now(timezone.utc)
    providers: list[dict] = []
    for provider in CATALOG.providers:
        operation = operations.get(provider.id)
        last_ingested_at = operation.last_ingested_at if operation and operation.last_ingested_at else latest.get(provider.id)
        if last_ingested_at and last_ingested_at.tzinfo is None:
            last_ingested_at = last_ingested_at.replace(tzinfo=timezone.utc)
        stale = bool(last_ingested_at and (now - last_ingested_at).total_seconds() > provider.freshness_sla_seconds)
        rollout_state = operation.rollout_state if operation else provider.rollout_state
        capability = next((category.capability for category in CATALOG.categories if category.id == provider.category_id), "provider_observations")
        live = rollout_state == "verified" and capability != "development_preview" and not stale
        current_capability = "live" if live else "preview" if capability == "development_preview" else "degraded" if stale else "unavailable"
        providers.append({
            "provider_id": provider.id,
            "name": provider.name,
            "category_id": provider.category_id,
            "rollout_state": "degraded" if stale and rollout_state == "verified" else rollout_state,
            "current_capability": current_capability,
            "live": live,
            "last_ingested_at": last_ingested_at,
            "freshness_sla_seconds": provider.freshness_sla_seconds,
            "stale": stale,
            "ingested_observations": int(counts.get(provider.id, 0)),
            "parser_success_rate": 1.0 if counts.get(provider.id, 0) else 0.0,
            "timeout_rate": None,
            "exact_match_success_rate": None,
            "failure_reason": operation.failure_reason if operation else None,
        })
    return {"generated_at": now.isoformat(), "providers": providers}
