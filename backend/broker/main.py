from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import FastAPI, Header, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import select

from app.category_catalog import PROVIDERS_BY_ID
from broker.adapters import ConfiguredOAuthAdapter
from broker.config import settings
from broker.models import BrokerSession, VaultCredential
from broker.vault import TokenVault

app = FastAPI(title="TrueCost Provider Broker", docs_url=None, redoc_url=None)
redis = Redis.from_url(settings.redis_url, decode_responses=True)


def _adapter(provider_id: str) -> ConfiguredOAuthAdapter:
    if provider_id not in settings.enabled_provider_ids or provider_id not in PROVIDERS_BY_ID:
        raise HTTPException(status_code=503, detail="Provider connection is pending official approval")
    adapter = ConfiguredOAuthAdapter(provider_id)
    if not adapter.configured:
        raise HTTPException(status_code=503, detail="Provider connection is not configured")
    return adapter


def _challenge(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def _signature_payload(provider_id: str, original_state: str, result: str, account_label: str, expires_at: str) -> str:
    return "|".join((provider_id, original_state, result, account_label, expires_at))


@app.on_event("startup")
def startup() -> None:
    if len(settings.callback_secret) < 32:
        raise RuntimeError("BROKER_CALLBACK_SECRET must be at least 32 characters")


@app.get("/authorize")
async def authorize(provider: str, state: str = Query(min_length=32, max_length=200), redirect_uri: str = Query(max_length=300)):
    if redirect_uri not in settings.redirect_allowlist:
        raise HTTPException(status_code=400, detail="Redirect URI is not allowed")
    adapter = _adapter(provider)
    nonce = secrets.token_urlsafe(40)
    verifier = secrets.token_urlsafe(64)
    callback_uri = f"{settings.public_url.rstrip('/')}/callback/{provider}"
    payload = {"provider": provider, "original_state": state, "mobile_redirect": redirect_uri, "verifier": verifier}
    await redis.set(f"oauth-state:{nonce}", json.dumps(payload), ex=600, nx=True)
    return RedirectResponse(adapter.authorization_url(state=nonce, challenge=_challenge(verifier), redirect_uri=callback_uri), status_code=302)


@app.get("/callback/{provider_id}")
async def callback(provider_id: str, code: str = Query(min_length=1), state: str = Query(min_length=32)):
    raw = await redis.getdel(f"oauth-state:{state}")
    if raw is None:
        raise HTTPException(status_code=401, detail="OAuth state is invalid, expired, or already used")
    pending = json.loads(raw)
    if pending["provider"] != provider_id:
        raise HTTPException(status_code=401, detail="OAuth provider does not match the attempt")
    adapter = _adapter(provider_id)
    callback_uri = f"{settings.public_url.rstrip('/')}/callback/{provider_id}"
    tokens = await adapter.exchange(code=code, verifier=pending["verifier"], redirect_uri=callback_uri)
    subject_ref = hashlib.sha256(pending["original_state"].encode()).hexdigest()
    vault = TokenVault(settings.vault_encryption_keys)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens.expires_in) if tokens.expires_in else None
    with BrokerSession() as db:
        row = db.scalar(select(VaultCredential).where(VaultCredential.subject_ref == subject_ref))
        if row is None:
            row = VaultCredential(subject_ref=subject_ref, provider_id=provider_id, access_token_ciphertext=b"")
            db.add(row)
        row.access_token_ciphertext = vault.seal(tokens.access_token) or b""
        row.refresh_token_ciphertext = vault.seal(tokens.refresh_token)
        row.scopes = " ".join(tokens.scopes)
        row.expires_at = expires_at
        row.revoked_at = None
        db.commit()
    expiry = expires_at.isoformat() if expires_at else ""
    signature = hmac.new(settings.callback_secret.encode(), _signature_payload(provider_id, pending["original_state"], "connected", "", expiry).encode(), hashlib.sha256).hexdigest()
    query = urlencode({"provider_id": provider_id, "state": pending["original_state"], "result": "connected", "expires_at": expiry, "signature": signature})
    return RedirectResponse(f"{pending['mobile_redirect']}?{query}", status_code=302)


class RevokeInput(BaseModel):
    subject_ref: str
    provider_id: str
    timestamp: int


@app.post("/internal/revoke", status_code=204)
async def revoke(payload: RevokeInput, x_broker_signature: str = Header(default="")) -> None:
    if abs(int(datetime.now(timezone.utc).timestamp()) - payload.timestamp) > 60:
        raise HTTPException(status_code=401, detail="Request timestamp expired")
    signed = f"{payload.subject_ref}|{payload.provider_id}|{payload.timestamp}"
    expected = hmac.new(settings.callback_secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_broker_signature):
        raise HTTPException(status_code=401, detail="Invalid internal signature")
    adapter = _adapter(payload.provider_id)
    vault = TokenVault(settings.vault_encryption_keys)
    with BrokerSession() as db:
        row = db.scalar(select(VaultCredential).where(VaultCredential.subject_ref == payload.subject_ref, VaultCredential.provider_id == payload.provider_id))
        if row and row.revoked_at is None:
            await adapter.revoke(vault.open(row.refresh_token_ciphertext) or vault.open(row.access_token_ciphertext) or "")
            row.revoked_at = datetime.now(timezone.utc)
            db.commit()
