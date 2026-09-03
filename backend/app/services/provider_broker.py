from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone

import httpx

from app.config import settings


class ProviderBrokerClient:
    def revoke(self, subject_ref: str, provider_id: str) -> None:
        if not settings.provider_connection_broker_url or not settings.provider_connection_broker_secret:
            raise RuntimeError("Provider broker is not configured")
        timestamp = int(datetime.now(timezone.utc).timestamp())
        signed = f"{subject_ref}|{provider_id}|{timestamp}"
        signature = hmac.new(settings.provider_connection_broker_secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
        response = httpx.post(
            f"{settings.provider_connection_broker_url.rstrip('/')}/internal/revoke",
            headers={"X-Broker-Signature": signature},
            json={"subject_ref": subject_ref, "provider_id": provider_id, "timestamp": timestamp},
            timeout=15,
        )
        response.raise_for_status()
