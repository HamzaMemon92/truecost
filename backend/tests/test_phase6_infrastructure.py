from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.api.endpoints import auth as auth_endpoint
from app.db import Base, get_db
from app.main import app
from app.models import Notification, NotificationOutbox, PriceObservation, PriceWatchTrigger, PushDevice
from app.services.price_watcher import evaluate_active_price_watches


class CapturingSmsProvider:
    def __init__(self) -> None:
        self.messages: dict[str, str] = {}

    def send_otp(self, phone_number: str, code: str, expires_minutes: int) -> None:
        self.messages[phone_number] = code


class CapturingPushService:
    def __init__(self) -> None:
        self.messages = []

    def send(self, messages):
        self.messages.extend(messages)
        return [{"status": "ok", "id": f"ticket-{index}"} for index, _ in enumerate(messages)]


@pytest.fixture()
def infrastructure(tmp_path, monkeypatch) -> Iterator[tuple[TestClient, sessionmaker, CapturingSmsProvider]]:
    test_engine = create_engine(f"sqlite:///{tmp_path / 'phase6.db'}", connect_args={"check_same_thread": False})
    test_session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        with test_session() as db:
            yield db

    sms = CapturingSmsProvider()
    monkeypatch.setattr(auth_endpoint, "sms_provider", sms)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, test_session, sms
    app.dependency_overrides.clear()
    test_engine.dispose()


def test_otp_is_one_time_hashed_and_issues_a_phone_session(infrastructure) -> None:
    client, test_session, sms = infrastructure
    phone = "+919876543210"
    requested = client.post("/api/v1/auth/request-otp", json={"phone_number": phone})
    assert requested.status_code == 202, requested.text
    assert "code" not in requested.json()
    challenge_id = requested.json()["challenge_id"]

    wrong = client.post("/api/v1/auth/verify-otp", json={"challenge_id": challenge_id, "code": "000000"})
    assert wrong.status_code == 401
    verified = client.post("/api/v1/auth/verify-otp", json={"challenge_id": challenge_id, "code": sms.messages[phone]})
    assert verified.status_code == 200, verified.text
    headers = {"Authorization": f"Bearer {verified.json()['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["phone_number"] == phone
    assert me.json()["email"] is None
    assert client.post("/api/v1/auth/verify-otp", json={"challenge_id": challenge_id, "code": sms.messages[phone]}).status_code == 401

    with test_session() as db:
        challenge = db.get(auth_endpoint.OtpChallenge, challenge_id)
        assert challenge.code_hash != sms.messages[phone]
        assert challenge.consumed_at is not None


def test_push_token_registration_is_authenticated_and_owned(infrastructure) -> None:
    client, test_session, _ = infrastructure
    tokens = client.post("/api/v1/auth/register", json={"email": "push@example.com", "password": "a-strong-password"}).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    token = "ExponentPushToken[phase6_test_device_123]"
    assert client.post("/api/v1/auth/push-tokens", json={"expo_push_token": token, "platform": "android"}).status_code == 401
    created = client.post("/api/v1/auth/push-tokens", headers=headers, json={"expo_push_token": token, "platform": "android", "device_name": "Test device"})
    assert created.status_code == 200, created.text
    device_id = created.json()["id"]
    assert client.delete(f"/api/v1/auth/push-tokens/{device_id}", headers=headers).status_code == 204
    with test_session() as db:
        assert db.get(PushDevice, device_id).active is False


def test_price_watch_trigger_is_idempotent_and_sends_push(infrastructure) -> None:
    client, test_session, _ = infrastructure
    tokens = client.post("/api/v1/auth/register", json={"email": "watcher@example.com", "password": "a-strong-password"}).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    client.post("/api/v1/auth/push-tokens", headers=headers, json={"expo_push_token": "ExponentPushToken[watch_device_123456]", "platform": "ios"})
    watch = client.post("/api/v1/commerce/price-watches", headers=headers, json={"title": "Headphones", "target_price": 5000, "current_price": 6200}).json()
    with test_session() as db:
        db.add(PriceObservation(watch_id=watch["id"], provider="Observed store", price=4800))
        db.commit()

    push = CapturingPushService()
    first = evaluate_active_price_watches(test_session, push_service=push)
    second = evaluate_active_price_watches(test_session, push_service=push)
    assert first.triggered == 1
    assert second.triggered == 0
    assert len(push.messages) == 1
    assert push.messages[0].data["watchId"] == watch["id"]

    with test_session() as db:
        db.add(PriceObservation(watch_id=watch["id"], provider="Observed store", price=5600))
        db.commit()
    assert evaluate_active_price_watches(test_session, push_service=push).triggered == 0
    with test_session() as db:
        db.add(PriceObservation(watch_id=watch["id"], provider="Observed store", price=4700))
        db.commit()
    assert evaluate_active_price_watches(test_session, push_service=push).triggered == 1
    assert len(push.messages) == 2

    with test_session() as db:
        assert db.scalar(select(func.count()).select_from(PriceWatchTrigger)) == 2
        assert db.scalar(select(func.count()).select_from(NotificationOutbox)) == 2
        triggered = db.scalar(select(Notification).where(Notification.title.like("Target reached:%")))
        assert triggered is not None
        assert "4800" in triggered.body
