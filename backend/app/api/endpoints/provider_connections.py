from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.endpoints.auth import current_user
from app.config import settings
from app.db import get_db
from app.models import BrokerRevocationOutbox, ProviderConnection, ProviderConnectionAttempt, ProviderOperationalState, User, UserActivity
from app.services.provider_broker import ProviderBrokerClient
from app.category_catalog import PROVIDERS_BY_ID

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(current_user)]
CALLBACK_URL = "truecost://provider-connect"

_CONNECTION_CANDIDATES = ("amazon", "flipkart", "swiggy", "zepto", "blinkit", "uber", "ola", "rapido")
_BRAND_PRESENTATION = {
    "amazon": ("#FF9900", "a"), "flipkart": ("#2874F0", "F"), "swiggy": ("#FC8019", "S"),
    "zepto": ("#5B2EFF", "Z"), "blinkit": ("#F8CB46", "B"), "uber": ("#111111", "U"),
    "ola": ("#2DBB54", "O"), "rapido": ("#F9C935", "R"),
}
PROVIDERS = [
    {
        "id": provider_id,
        "name": "Swiggy" if provider_id == "swiggy" else PROVIDERS_BY_ID[provider_id].name,
        "category": "Food & Grocery" if provider_id == "swiggy" else PROVIDERS_BY_ID[provider_id].category_id.title(),
        "brand_color": _BRAND_PRESENTATION[provider_id][0],
        "mark": _BRAND_PRESENTATION[provider_id][1],
        "catalog_connection_state": PROVIDERS_BY_ID[provider_id].account_connection_state,
    }
    for provider_id in _CONNECTION_CANDIDATES
]
PROVIDER_BY_ID = {provider["id"]: provider for provider in PROVIDERS}


class ConnectionResponse(BaseModel):
    id: str
    name: str
    category: str
    brand_color: str
    mark: str
    status: Literal["disconnected", "connecting", "connected", "expired"]
    connection_supported: bool
    account_label: str | None = None
    connected_at: datetime | None = None
    expires_at: datetime | None = None


class ConnectionStartResponse(BaseModel):
    authorization_url: str
    callback_url: str = CALLBACK_URL
    expires_at: datetime


class ConnectionCompleteInput(BaseModel):
    provider_id: str = Field(max_length=80)
    state: str = Field(min_length=32, max_length=200)
    result: Literal["connected", "expired", "cancelled"]
    account_label: str | None = Field(default=None, max_length=160)
    expires_at: datetime | None = None
    signature: str = Field(min_length=64, max_length=64)

    @field_validator("account_label")
    @classmethod
    def require_masked_identifier(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if ("@" in value and "*" not in value) or re.search(r"\d{7,}", value):
            raise ValueError("Provider account identifiers must be masked")
        return value or None


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _state_hash(state: str) -> str:
    return hashlib.sha256(state.encode()).hexdigest()


def _signature_payload(payload: ConnectionCompleteInput) -> str:
    expiry = payload.expires_at.astimezone(timezone.utc).isoformat() if payload.expires_at else ""
    return "|".join((payload.provider_id, payload.state, payload.result, payload.account_label or "", expiry))


def _response(provider: dict, row: ProviderConnection | None, connection_enabled: bool = False) -> ConnectionResponse:
    connection_status = "disconnected"
    if row and row.status == "connected":
        connection_status = "expired" if row.expires_at and _as_utc(row.expires_at) <= datetime.now(timezone.utc) else "connected"
    elif row and row.status == "expired":
        connection_status = "expired"
    elif row and row.status == "revocation_pending":
        connection_status = "connecting"
    public_provider = {key: value for key, value in provider.items() if key != "catalog_connection_state"}
    return ConnectionResponse(
        **public_provider,
        status=connection_status,
        connection_supported=bool(connection_enabled and settings.provider_connection_broker_url and settings.provider_connection_broker_secret),
        account_label=row.account_label if row else None,
        connected_at=row.connected_at if row else None,
        expires_at=row.expires_at if row else None,
    )


@router.get("", response_model=list[ConnectionResponse])
def list_connections(db: Db, user: CurrentUser) -> list[ConnectionResponse]:
    rows = {row.provider_id: row for row in db.scalars(select(ProviderConnection).where(ProviderConnection.user_id == user.id)).all()}
    enabled = {row.provider_id for row in db.scalars(select(ProviderOperationalState).where(ProviderOperationalState.connection_state == "enabled")).all()}
    return [_response(provider, rows.get(provider["id"]), provider["id"] in enabled) for provider in PROVIDERS]


@router.post("/{provider_id}/start", response_model=ConnectionStartResponse)
def start_connection(provider_id: str, db: Db, user: CurrentUser) -> ConnectionStartResponse:
    if provider_id not in PROVIDER_BY_ID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider connection is not supported")
    operation = db.get(ProviderOperationalState, provider_id)
    if operation is None or operation.connection_state != "enabled" or not settings.provider_connection_broker_url or not settings.provider_connection_broker_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Official account connection is not configured for this environment")
    raw_state = secrets.token_urlsafe(40)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.provider_connection_attempt_minutes)
    db.add(ProviderConnectionAttempt(user_id=user.id, provider_id=provider_id, state_hash=_state_hash(raw_state), expires_at=expires_at))
    db.commit()
    query = urlencode({"provider": provider_id, "state": raw_state, "redirect_uri": CALLBACK_URL})
    url = f"{settings.provider_connection_broker_url.rstrip('/')}/authorize?{query}"
    return ConnectionStartResponse(authorization_url=url, expires_at=expires_at)


@router.post("/complete", response_model=ConnectionResponse)
def complete_connection(payload: ConnectionCompleteInput, db: Db, user: CurrentUser) -> ConnectionResponse:
    provider = PROVIDER_BY_ID.get(payload.provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider connection is not supported")
    if not settings.provider_connection_broker_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Official account connection is not configured")
    attempt = db.scalar(select(ProviderConnectionAttempt).where(ProviderConnectionAttempt.state_hash == _state_hash(payload.state), ProviderConnectionAttempt.user_id == user.id, ProviderConnectionAttempt.provider_id == payload.provider_id))
    now = datetime.now(timezone.utc)
    if attempt is None or attempt.consumed_at is not None or _as_utc(attempt.expires_at) <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Connection attempt is invalid or expired")
    expected = hmac.new(settings.provider_connection_broker_secret.encode(), _signature_payload(payload).encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, payload.signature.lower()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Connection result could not be verified")
    attempt.consumed_at = now
    row = db.scalar(select(ProviderConnection).where(ProviderConnection.user_id == user.id, ProviderConnection.provider_id == payload.provider_id))
    if payload.result == "cancelled":
        db.commit()
        return _response(provider, row)
    if row is None:
        row = ProviderConnection(user_id=user.id, provider_id=payload.provider_id)
        db.add(row)
    row.status = "connected" if payload.result == "connected" else "expired"
    row.broker_subject_ref = _state_hash(payload.state) if payload.result == "connected" else row.broker_subject_ref
    row.account_label = payload.account_label if payload.result == "connected" else None
    row.connected_at = now
    row.expires_at = payload.expires_at
    db.add(UserActivity(user_id=user.id, event_type="provider_connection.updated", title=f"Updated {provider['name']} connection", details={"provider_id": payload.provider_id, "status": row.status}))
    db.commit()
    db.refresh(row)
    return _response(provider, row)


@router.delete("/{provider_id}", response_model=ConnectionResponse)
def disconnect_provider(provider_id: str, db: Db, user: CurrentUser) -> ConnectionResponse:
    provider = PROVIDER_BY_ID.get(provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider connection is not supported")
    row = db.scalar(select(ProviderConnection).where(ProviderConnection.user_id == user.id, ProviderConnection.provider_id == provider_id))
    if row:
        if row.broker_subject_ref:
            try:
                ProviderBrokerClient().revoke(row.broker_subject_ref, provider_id)
                db.delete(row)
            except Exception:
                row.status = "revocation_pending"
                pending = db.scalar(select(BrokerRevocationOutbox).where(BrokerRevocationOutbox.connection_id == row.id))
                if pending is None:
                    db.add(BrokerRevocationOutbox(connection_id=row.id, user_id=user.id, provider_id=provider_id, subject_ref=row.broker_subject_ref))
        else:
            db.delete(row)
        db.add(UserActivity(user_id=user.id, event_type="provider_connection.disconnected", title=f"Disconnect requested for {provider['name']}", details={"provider_id": provider_id}))
        db.commit()
    return _response(provider, row if row and row.status == "revocation_pending" else None)
