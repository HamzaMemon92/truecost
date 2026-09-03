from __future__ import annotations

from typing import Annotated, Literal
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.endpoints.auth import require_admin
from app.db import get_db
from app.models import IngestedProviderResult, NotificationOutbox, ProviderOperationalState, ProviderVerificationEvent, User
from app.category_catalog import PROVIDERS_BY_ID
from app.config import settings
from app.services.cache import cache

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]
Admin = Annotated[User, Depends(require_admin)]


class ProviderStatePatch(BaseModel):
    rollout_state: Literal["catalogued", "testing", "verified", "degraded", "disabled"] | None = None
    connection_state: Literal["pending_approval", "enabled", "unavailable"] | None = None
    failure_reason: str | None = None


class ProviderVerificationInput(BaseModel):
    verification_kind: Literal["ingestion", "oauth"]
    checks: dict[str, bool]


@router.get("/operations")
def operations(db: Db, _: Admin) -> dict:
    provider_states = db.scalars(select(ProviderOperationalState).order_by(ProviderOperationalState.provider_id)).all()
    outbox = dict(db.execute(select(NotificationOutbox.status, func.count()).group_by(NotificationOutbox.status)).all())
    ingested = db.scalar(select(func.count()).select_from(IngestedProviderResult)) or 0
    worker: dict = {"mode": settings.task_execution_mode}
    if settings.task_execution_mode == "celery":
        try:
            from redis import Redis
            client = Redis.from_url(settings.redis_url)
            worker["broker_reachable"] = bool(client.ping())
            worker["queue_depth"] = int(client.llen("celery"))
        except Exception as exc:
            worker.update({"broker_reachable": False, "error": type(exc).__name__})
    return {
        "providers": [{"provider_id": row.provider_id, "rollout_state": row.rollout_state, "connection_state": row.connection_state, "last_ingested_at": row.last_ingested_at, "failure_reason": row.failure_reason} for row in provider_states],
        "notification_outbox": outbox,
        "ingested_observations": ingested,
        "cache": cache.stats(),
        "worker": worker,
    }


@router.put("/providers/{provider_id}")
def update_provider_state(provider_id: str, payload: ProviderStatePatch, db: Db, _: Admin) -> dict:
    if provider_id not in PROVIDERS_BY_ID:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Provider is not catalogued")
    row = db.get(ProviderOperationalState, provider_id)
    if row is None:
        row = ProviderOperationalState(provider_id=provider_id)
        db.add(row)
    if payload.rollout_state is not None:
        if payload.rollout_state == "verified":
            passed = db.scalar(select(ProviderVerificationEvent.id).where(ProviderVerificationEvent.provider_id == provider_id, ProviderVerificationEvent.verification_kind == "ingestion", ProviderVerificationEvent.passed.is_(True)).order_by(ProviderVerificationEvent.created_at.desc()).limit(1))
            if passed is None:
                from fastapi import HTTPException
                raise HTTPException(status_code=409, detail="A passing ingestion verification is required before rollout")
        row.rollout_state = payload.rollout_state
    if payload.connection_state is not None:
        if payload.connection_state == "enabled":
            passed = db.scalar(select(ProviderVerificationEvent.id).where(ProviderVerificationEvent.provider_id == provider_id, ProviderVerificationEvent.verification_kind == "oauth", ProviderVerificationEvent.passed.is_(True)).order_by(ProviderVerificationEvent.created_at.desc()).limit(1))
            if passed is None:
                from fastapi import HTTPException
                raise HTTPException(status_code=409, detail="A passing official OAuth verification is required before connections can be enabled")
        row.connection_state = payload.connection_state
    if "failure_reason" in payload.model_fields_set:
        row.failure_reason = payload.failure_reason
    db.commit()
    return {"provider_id": row.provider_id, "rollout_state": row.rollout_state, "connection_state": row.connection_state, "failure_reason": row.failure_reason}


@router.post("/providers/{provider_id}/verification", status_code=201)
def record_provider_verification(provider_id: str, payload: ProviderVerificationInput, db: Db, admin: Admin) -> dict:
    if provider_id not in PROVIDERS_BY_ID:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Provider is not catalogued")
    required = {"normalization", "provenance", "handoff", "timeouts", "partial_failure"} if payload.verification_kind == "ingestion" else {"official_credentials", "approved_scopes", "redirect_registered", "contract_tests"}
    passed = required.issubset(payload.checks) and all(payload.checks.get(check) is True for check in required)
    event = ProviderVerificationEvent(provider_id=provider_id, verification_kind=payload.verification_kind, checks=payload.checks, passed=passed, recorded_by_user_id=admin.id)
    db.add(event)
    if passed and payload.verification_kind == "ingestion":
        row = db.get(ProviderOperationalState, provider_id) or ProviderOperationalState(provider_id=provider_id)
        row.last_verified_at = datetime.now(timezone.utc)
        db.add(row)
    db.commit()
    return {"id": event.id, "provider_id": provider_id, "verification_kind": payload.verification_kind, "passed": passed, "checks": payload.checks}
from typing import Optional

@router.get("/entity-resolution/shadow/metrics")
def shadow_metrics(
    db: Db,
    _: Admin,
    provider: Optional[str] = None,
    category: Optional[str] = None,
    resolver_version: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> dict:
    from app.services.entity_resolution_metrics import EntityResolutionMetricsService
    service = EntityResolutionMetricsService(db)
    return service.get_metrics(
        provider=provider,
        category=category,
        resolver_version=resolver_version,
        start_time=start_time,
        end_time=end_time
    )

@router.get("/entity-resolution/shadow/disagreements")
def shadow_disagreements(
    db: Db,
    _: Admin,
    provider: Optional[str] = None,
    category: Optional[str] = None,
    legacy_decision: Optional[str] = None,
    v3_decision: Optional[str] = None,
    missing_factor: Optional[str] = None,
    conflict_factor: Optional[str] = None,
    resolver_version: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> list[dict]:
    from app.services.entity_resolution_metrics import EntityResolutionMetricsService
    service = EntityResolutionMetricsService(db)
    return service.get_disagreements(
        provider=provider,
        category=category,
        legacy_decision=legacy_decision,
        v3_decision=v3_decision,
        missing_factor=missing_factor,
        conflict_factor=conflict_factor,
        resolver_version=resolver_version,
        limit=limit,
        offset=offset
    )
from typing import Optional
from fastapi import Query
from pydantic import BaseModel

from enum import Enum

class ReviewLabel(str, Enum):
    V3_CORRECT = "V3_CORRECT"
    LEGACY_CORRECT = "LEGACY_CORRECT"
    BOTH_CORRECT = "BOTH_CORRECT"
    BOTH_WRONG = "BOTH_WRONG"
    AMBIGUOUS = "AMBIGUOUS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class ReviewErrorClassification(str, Enum):
    FALSE_MERGE = "FALSE_MERGE"
    FALSE_REJECT = "FALSE_REJECT"
    WRONG_PROBABLE = "WRONG_PROBABLE"
    WRONG_RELATED = "WRONG_RELATED"
    NORMALIZATION_FAILURE = "NORMALIZATION_FAILURE"
    EXTRACTION_FAILURE = "EXTRACTION_FAILURE"
    SOURCE_DATA_FAILURE = "SOURCE_DATA_FAILURE"
    CONTRACT_FAILURE = "CONTRACT_FAILURE"

class ReviewPayload(BaseModel):
    review_label: ReviewLabel
    review_error_classification: Optional[ReviewErrorClassification] = None
    review_notes: Optional[str] = None

@router.get("/entity-resolution/shadow/metrics")
def shadow_metrics(
    db: Db,
    admin: Admin,
    provider: Optional[str] = None,
    category: Optional[str] = None,
    resolver_version: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> dict:
    from app.services.entity_resolution_metrics import EntityResolutionMetricsService
    service = EntityResolutionMetricsService(db)
    return service.get_metrics(
        provider=provider,
        category=category,
        resolver_version=resolver_version,
        start_time=start_time,
        end_time=end_time
    )

@router.get("/entity-resolution/shadow/disagreements")
def shadow_disagreements(
    db: Db,
    admin: Admin,
    provider: Optional[str] = None,
    category: Optional[str] = None,
    legacy_decision: Optional[str] = None,
    v3_decision: Optional[str] = None,
    missing_factor: Optional[str] = None,
    conflict_factor: Optional[str] = None,
    resolver_version: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> list[dict]:
    from app.services.entity_resolution_metrics import EntityResolutionMetricsService
    service = EntityResolutionMetricsService(db)
    return service.get_disagreements(
        provider=provider,
        category=category,
        legacy_decision=legacy_decision,
        v3_decision=v3_decision,
        missing_factor=missing_factor,
        conflict_factor=conflict_factor,
        resolver_version=resolver_version,
        limit=limit,
        offset=offset
    )

@router.post("/entity-resolution/shadow/records/{record_id}/review")
def review_record(
    record_id: str,
    payload: ReviewPayload,
    db: Db,
    admin: Admin
) -> dict:
    from fastapi import HTTPException
    from app.services.entity_resolution_metrics import EntityResolutionMetricsService
    service = EntityResolutionMetricsService(db)
    try:
        success = service.add_review(
            record_id=record_id,
            label=payload.review_label.value,
            error_class=payload.review_error_classification.value if payload.review_error_classification else None,
            notes=payload.review_notes,
            admin_id=admin.id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Record not found")
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
