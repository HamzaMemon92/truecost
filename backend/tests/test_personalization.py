from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def isolated_database(tmp_path) -> Iterator[None]:
    engine = create_engine(f"sqlite:///{tmp_path / 'personalization.db'}", connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    def override():
        db = factory()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override
    yield
    app.dependency_overrides.clear(); engine.dispose()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as value:
        yield value


def auth(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "a-strong-password"})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_typed_preferences_merge_without_clobbering_existing_profile(client: TestClient) -> None:
    headers = auth(client, "preferences@example.com")
    client.put("/api/v1/profiles/me", headers=headers, json={"display_name": "Anas", "preferences": {"currency": "INR", "legacy_safe": True}})
    response = client.patch("/api/v1/profiles/me/preferences", headers=headers, json={
        "objective": "balanced",
        "preferred_categories": ["Grocery", "Shopping", "Services"],
        "dietary": ["vegetarian", "low_sugar"],
        "notification_preferences": {"price_drops": True, "travel_alerts": False},
        "accessibility": {"reduced_motion": True},
        "privacy": {"product_analytics": False},
    })
    assert response.status_code == 200, response.text
    preferences = response.json()["preferences"]
    assert preferences["currency"] == "INR"
    assert preferences["legacy_safe"] is True
    assert preferences["objective"] == "balanced"
    assert preferences["notification_preferences"]["travel_alerts"] is False
    second = client.patch("/api/v1/profiles/me/preferences", headers=headers, json={"notification_preferences": {"deals": True}})
    assert second.json()["preferences"]["notification_preferences"]["price_drops"] is True
    assert client.patch("/api/v1/profiles/me/preferences", headers=headers, json={"objective": "random"}).status_code == 422
    assert client.patch("/api/v1/profiles/me/preferences", headers=headers, json={"preferred_categories": ["Imaginary"]}).status_code == 422


def test_saved_addresses_default_activation_serviceability_and_ownership(client: TestClient) -> None:
    owner = auth(client, "address@example.com"); other = auth(client, "address-other@example.com")
    home = client.post("/api/v1/profiles/me/addresses", headers=owner, json={
        "label": "Home", "address_line": "12 Main Road", "city": "Bengaluru", "state": "Karnataka",
        "postal_code": "560001", "country_code": "IN", "latitude": 12.9716, "longitude": 77.5946,
    })
    assert home.status_code == 201, home.text
    assert home.json()["is_default"] is True
    work = client.post("/api/v1/profiles/me/addresses", headers=owner, json={
        "label": "Work", "address_line": "42 Market Street", "locality": "Central", "city": "Bengaluru",
        "postal_code": "560002", "latitude": 12.98, "longitude": 77.61,
    }).json()
    assert work["is_default"] is False
    activated = client.post(f"/api/v1/profiles/me/addresses/{work['id']}/activate", headers=owner)
    assert activated.status_code == 200 and activated.json()["is_default"] is True
    addresses = client.get("/api/v1/profiles/me/addresses", headers=owner).json()
    assert addresses[0]["id"] == work["id"]
    assert sum(item["is_default"] for item in addresses) == 1
    serviceability = client.get(f"/api/v1/profiles/me/serviceability?address_id={work['id']}&category=Grocery", headers=owner)
    assert serviceability.status_code == 200
    assert serviceability.json()["status"] == "verification_required"
    assert serviceability.json()["checked_providers"] == []
    assert client.post(f"/api/v1/profiles/me/addresses/{work['id']}/activate", headers=other).status_code == 404


def test_payment_preferences_store_only_safe_masked_metadata(client: TestClient) -> None:
    owner = auth(client, "payments@example.com"); other = auth(client, "payments-other@example.com")
    unsafe = client.post("/api/v1/profiles/me/payment-preferences", headers=owner, json={
        "method_type": "card", "label": "Unsafe", "last4": "1234", "card_number": "4111111111111111",
    })
    assert unsafe.status_code == 422
    raw_upi = client.post("/api/v1/profiles/me/payment-preferences", headers=owner, json={"method_type": "upi", "label": "Personal UPI", "masked_identifier": "person@bank"})
    assert raw_upi.status_code == 422
    card = client.post("/api/v1/profiles/me/payment-preferences", headers=owner, json={
        "method_type": "card", "label": "Everyday card", "issuer": "Example Bank", "network": "Visa", "last4": "4242", "benefit_tags": ["cashback eligible"],
    })
    assert card.status_code == 201, card.text
    assert card.json()["masked_identifier"].endswith("4242")
    assert "card_number" not in card.json()
    assert card.json()["is_preferred"] is True
    upi = client.post("/api/v1/profiles/me/payment-preferences", headers=owner, json={"method_type": "upi", "label": "Primary UPI", "masked_identifier": "a***@bank"})
    assert upi.status_code == 201, upi.text
    preferred = client.post(f"/api/v1/profiles/me/payment-preferences/{upi.json()['id']}/prefer", headers=owner)
    assert preferred.status_code == 200 and preferred.json()["is_preferred"] is True
    methods = client.get("/api/v1/profiles/me/payment-preferences", headers=owner).json()
    assert sum(item["is_preferred"] for item in methods) == 1
    assert client.delete(f"/api/v1/profiles/me/payment-preferences/{card.json()['id']}", headers=other).status_code == 404


def test_category_catalog_is_explicit_about_capability_and_availability(client: TestClient) -> None:
    headers = auth(client, "catalog@example.com")
    response = client.get("/api/v1/commerce/catalog/categories", headers=headers)
    assert response.status_code == 200, response.text
    categories = response.json()
    assert {item["name"] for item in categories} == {
        "Grocery", "Food", "Pharmacy", "Shopping", "Mobility", "Flights", "Hotels", "Deals", "Finance", "Services"
    }
    assert all(item["availability_verified"] is False for item in categories)
    services = next(item for item in categories if item["name"] == "Services")
    assert services["engine_category"] == "Productivity"
    public_catalog = client.get("/api/v1/providers")
    assert public_catalog.status_code == 200
    assert len(public_catalog.json()["providers"]) == 32
    assert all(provider["live"] is False for provider in public_catalog.json()["providers"])


def test_privacy_and_notification_preferences_change_commerce_side_effects(client: TestClient) -> None:
    headers = auth(client, "privacy@example.com")
    preference_response = client.patch("/api/v1/profiles/me/preferences", headers=headers, json={
        "privacy": {"retain_activity": False},
        "notification_preferences": {"price_drops": False},
    })
    assert preference_response.status_code == 200, preference_response.text

    saved = client.post("/api/v1/commerce/saved-items", headers=headers, json={"title": "Private decision"})
    assert saved.status_code == 201, saved.text
    watch = client.post("/api/v1/commerce/price-watches", headers=headers, json={
        "title": "Quiet watch", "target_price": 99, "current_price": 120,
    })
    assert watch.status_code == 201, watch.text
    assert client.get("/api/v1/commerce/activity", headers=headers).json() == []
    assert client.get("/api/v1/commerce/notifications", headers=headers).json() == []
