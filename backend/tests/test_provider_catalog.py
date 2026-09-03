from app.category_catalog import CATALOG, normalize_provider_key
from app.api.endpoints.aggregator import KNOWN_PROVIDERS
from app.config import Settings
from app.main import app
from fastapi.testclient import TestClient
import pytest


def test_provider_catalog_has_exactly_32_unique_identities() -> None:
    identifiers = [provider.id for provider in CATALOG.providers]
    assert len(identifiers) == 32
    assert len(set(identifiers)) == 32
    assert set(identifiers) == set(KNOWN_PROVIDERS)


def test_aliases_and_flight_contract_are_canonical() -> None:
    assert normalize_provider_key("Swiggy Instamart") == "swiggy"
    assert normalize_provider_key("Swiggy Food") == "swiggy_food"
    travel = {provider.id for provider in CATALOG.providers if provider.category_id == "travel"}
    assert travel == {"makemytrip", "goibibo", "ixigo", "cleartrip"}
    assert "easemytrip" not in travel


def test_every_provider_starts_non_live() -> None:
    assert all(provider.rollout_state != "verified" for provider in CATALOG.providers)


def test_production_profile_fails_closed_without_required_infrastructure() -> None:
    with pytest.raises(ValueError):
        Settings(app_env="production", auth_secret_key="short", sms_provider="console")
    production = Settings(
        app_env="production",
        database_url="postgresql+psycopg://user:password@db/truecost",
        redis_url="rediss://redis.example.test/0",
        auth_secret_key="a-production-only-secret-that-is-long-enough",
        auto_create_schema=False,
        cors_origins="https://app.truecost.example",
        trusted_hosts="api.truecost.example",
        sms_provider="twilio",
        twilio_account_sid="sid",
        twilio_auth_token="token",
        twilio_from_number="+10000000000",
        task_execution_mode="celery",
        provider_preview_enabled=False,
        expo_access_token="expo-ci-token",
        provider_connection_broker_url="https://broker.truecost.example",
        provider_connection_broker_secret="a-broker-callback-secret-that-is-long-enough",
    )
    assert production.task_execution_mode == "celery"


def test_provider_health_public_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/providers/health")
    assert response.status_code == 200
    body = response.json()
    assert len(body["providers"]) == 32
    amazon = next(provider for provider in body["providers"] if provider["provider_id"] == "amazon")
    travel = next(provider for provider in body["providers"] if provider["provider_id"] == "makemytrip")
    assert amazon["live"] is False
    assert amazon["current_capability"] in {"unavailable", "degraded"}
    assert travel["live"] is False
    assert travel["current_capability"] == "preview"
