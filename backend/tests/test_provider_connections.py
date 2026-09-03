from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import Base, get_db
from app.main import app
from app.models import ProviderOperationalState
from app.services.provider_broker import ProviderBrokerClient


@pytest.fixture()
def client(tmp_path) -> Iterator[TestClient]:
    test_engine = create_engine(f"sqlite:///{tmp_path / 'provider-connections.db'}", connect_args={"check_same_thread": False})
    test_session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        with test_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    test_engine.dispose()


def auth_headers(client: TestClient) -> dict[str, str]:
    tokens = client.post("/api/v1/auth/register", json={"email": "connections@example.com", "password": "a-strong-password"}).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_catalog_is_authenticated_and_does_not_claim_unconfigured_oauth(client: TestClient) -> None:
    assert client.get("/api/v1/provider-connections").status_code == 401
    headers = auth_headers(client)
    catalog = client.get("/api/v1/provider-connections", headers=headers)
    assert catalog.status_code == 200
    assert {row["id"] for row in catalog.json()} >= {"amazon", "flipkart", "swiggy", "zepto", "uber"}
    assert all(row["status"] == "disconnected" for row in catalog.json())
    if not settings.provider_connection_broker_url:
        assert all(row["connection_supported"] is False for row in catalog.json())
        assert client.post("/api/v1/provider-connections/amazon/start", headers=headers).status_code == 503


def test_signed_one_time_broker_callback_connects_and_disconnects(client: TestClient, monkeypatch) -> None:
    secret = "test-only-provider-broker-secret"
    monkeypatch.setattr(settings, "provider_connection_broker_url", "https://connections.example.test")
    monkeypatch.setattr(settings, "provider_connection_broker_secret", secret)
    monkeypatch.setattr(ProviderBrokerClient, "revoke", lambda self, subject_ref, provider_id: None)
    override = app.dependency_overrides[get_db]
    with next(override()) as db:
        db.add(ProviderOperationalState(provider_id="swiggy", connection_state="enabled"))
        db.commit()
    headers = auth_headers(client)
    started = client.post("/api/v1/provider-connections/swiggy/start", headers=headers)
    assert started.status_code == 200, started.text
    query = parse_qs(urlparse(started.json()["authorization_url"]).query)
    state = query["state"][0]
    assert query["provider"] == ["swiggy"]
    assert query["redirect_uri"] == ["truecost://provider-connect"]

    expiry = (datetime.now(timezone.utc) + timedelta(days=30)).replace(microsecond=0)
    canonical = "|".join(("swiggy", state, "connected", "a***@example.com", expiry.isoformat()))
    payload = {
        "provider_id": "swiggy",
        "state": state,
        "result": "connected",
        "account_label": "a***@example.com",
        "expires_at": expiry.isoformat(),
        "signature": hashlib.sha256(b"wrong").hexdigest(),
    }
    assert client.post("/api/v1/provider-connections/complete", headers=headers, json=payload).status_code == 401
    payload["signature"] = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    completed = client.post("/api/v1/provider-connections/complete", headers=headers, json=payload)
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "connected"
    assert completed.json()["account_label"] == "a***@example.com"
    assert client.post("/api/v1/provider-connections/complete", headers=headers, json=payload).status_code == 401

    disconnected = client.delete("/api/v1/provider-connections/swiggy", headers=headers)
    assert disconnected.status_code == 200
    assert disconnected.json()["status"] == "disconnected"
