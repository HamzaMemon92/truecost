from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app
from app.models import IngestedProviderResult, SearchSession, User


@pytest.fixture(autouse=True)
def isolated_database(tmp_path) -> Iterator[None]:
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'commerce-test.db'}",
        connect_args={"check_same_thread": False},
    )
    test_session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield test_session
    app.dependency_overrides.clear()
    test_engine.dispose()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def headers_for(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "a-strong-password"})
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_saved_item_and_price_watch_are_authenticated_and_persisted(client: TestClient) -> None:
    assert client.get("/api/v1/commerce/saved-items").status_code == 401
    headers = headers_for(client, "commerce@example.com")

    saved = client.post("/api/v1/commerce/saved-items", headers=headers, json={
        "title": "Noise-cancelling headphones", "price": 5499, "provider": "Example", "metadata": {"color": "black"},
    })
    assert saved.status_code == 201, saved.text
    assert saved.json()["metadata"] == {"color": "black"}
    assert client.get("/api/v1/commerce/saved-items", headers=headers).json()[0]["id"] == saved.json()["id"]

    watch = client.post("/api/v1/commerce/price-watches", headers=headers, json={
        "title": "Headphones", "target_price": 5000, "current_price": 5499,
    })
    assert watch.status_code == 201, watch.text
    assert watch.json()["active"] is True
    updated = client.patch(f"/api/v1/commerce/price-watches/{watch.json()['id']}", headers=headers, json={
        "title": "Headphones", "target_price": 4800, "current_price": 5200, "active": False,
    })
    assert updated.status_code == 200
    assert updated.json()["target_price"] == 4800
    notifications = client.get("/api/v1/commerce/notifications", headers=headers)
    assert notifications.status_code == 200
    assert notifications.json()[0]["category"] == "price"
    assert notifications.json()[0]["read_at"] is None
    assert client.post(f"/api/v1/commerce/notifications/{notifications.json()[0]['id']}/read", headers=headers).status_code == 200
    assert client.post("/api/v1/commerce/notifications/mark-all-read", headers=headers).status_code == 204


def test_cart_items_dashboard_and_activity(client: TestClient) -> None:
    headers = headers_for(client, "cart@example.com")
    cart = client.post("/api/v1/commerce/carts", headers=headers, json={"name": "Office", "currency": "INR"})
    assert cart.status_code == 201, cart.text
    cart_id = cart.json()["id"]
    item = client.post(f"/api/v1/commerce/carts/{cart_id}/items", headers=headers, json={
        "title": "Keyboard", "quantity": 2, "unit_price": 1250.5, "metadata": {"switch": "brown"},
    })
    assert item.status_code == 201, item.text

    carts = client.get("/api/v1/commerce/carts", headers=headers)
    assert carts.status_code == 200
    assert carts.json()[0]["item_count"] == 2
    assert carts.json()[0]["estimated_total"] == 2501.0
    assert carts.json()[0]["items"][0]["metadata"] == {"switch": "brown"}

    summary = client.get("/api/v1/commerce/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["cart_count"] == 1
    assert summary.json()["cart_item_count"] == 2
    assert summary.json()["estimated_cart_total"] == 2501.0
    activities = client.get("/api/v1/commerce/activity?limit=1", headers=headers)
    assert activities.status_code == 200
    assert len(activities.json()) == 1
    assert activities.json()[0]["event_type"] == "cart_item.created"


def test_cross_user_resource_access_is_denied(client: TestClient) -> None:
    owner = headers_for(client, "owner@example.com")
    other = headers_for(client, "other@example.com")
    saved = client.post("/api/v1/commerce/saved-items", headers=owner, json={"title": "Private item"}).json()
    cart = client.post("/api/v1/commerce/carts", headers=owner, json={"name": "Private cart"}).json()
    cart_item = client.post(f"/api/v1/commerce/carts/{cart['id']}/items", headers=owner, json={"title": "Private cart item"}).json()

    assert client.patch(f"/api/v1/commerce/saved-items/{saved['id']}", headers=other, json={"title": "Stolen"}).status_code == 404
    assert client.post(f"/api/v1/commerce/carts/{cart['id']}/items", headers=other, json={"title": "Stolen"}).status_code == 404
    assert client.delete(f"/api/v1/commerce/carts/{cart['id']}/items/{cart_item['id']}", headers=other).status_code == 404


def test_saved_collections_can_be_shared_without_exposing_owner(client: TestClient) -> None:
    owner = headers_for(client, "lists@example.com")
    other = headers_for(client, "lists-other@example.com")
    saved = client.post("/api/v1/commerce/saved-items", headers=owner, json={"title": "Weekend headphones", "price": 3999}).json()
    created = client.post("/api/v1/commerce/collections", headers=owner, json={"name": "Weekend picks", "description": "Shortlist for Saturday"})
    assert created.status_code == 201, created.text
    collection_id = created.json()["id"]

    added = client.post(f"/api/v1/commerce/collections/{collection_id}/items", headers=owner, json={"saved_item_id": saved["id"], "note": "Compare warranty"})
    assert added.status_code == 200, added.text
    assert added.json()["items"][0]["note"] == "Compare warranty"
    assert client.post(f"/api/v1/commerce/collections/{collection_id}/items", headers=owner, json={"saved_item_id": saved["id"]}).status_code == 409
    assert client.get("/api/v1/commerce/collections", headers=other).json() == []
    assert client.patch(f"/api/v1/commerce/collections/{collection_id}", headers=other, json={"name": "Taken"}).status_code == 404

    shared = client.post(f"/api/v1/commerce/collections/{collection_id}/share", headers=owner)
    assert shared.status_code == 200
    token = shared.json()["share_token"]
    public = client.get(f"/api/v1/commerce/shared-lists/{token}")
    assert public.status_code == 200
    assert public.json()["name"] == "Weekend picks"
    assert "user_id" not in public.json()
    assert "metadata" not in public.json()["items"][0]["item"]
    assert client.delete(f"/api/v1/commerce/collections/{collection_id}/share", headers=owner).status_code == 200
    assert client.get(f"/api/v1/commerce/shared-lists/{token}").status_code == 404


def test_comparison_history_activity_summary_and_notification_filters(client: TestClient, isolated_database) -> None:
    headers = headers_for(client, "history@example.com")
    client.post("/api/v1/commerce/price-watches", headers=headers, json={"title": "Flight to Goa", "target_price": 4200, "provider": "Observed fares"})
    with isolated_database() as db:
        user = db.scalar(select(User).where(User.email == "history@example.com"))
        search = SearchSession(user_id=user.id, query="BLR to GOI", category="Travel")
        db.add(search)
        db.flush()
        db.add_all([
            IngestedProviderResult(search_session_id=search.id, provider="Provider A", product_id="fare-1", product={"title": "Morning fare", "price": 5100}),
            IngestedProviderResult(search_session_id=search.id, provider="Provider B", product_id="fare-2", product={"title": "Evening fare", "price": 4800}),
        ])
        db.commit()

    history = client.get("/api/v1/commerce/comparisons?category=Travel", headers=headers)
    assert history.status_code == 200, history.text
    assert history.json()[0]["provider_count"] == 2
    assert history.json()[0]["result_count"] == 2
    detail = client.get(f"/api/v1/commerce/comparisons/{history.json()[0]['id']}", headers=headers)
    assert detail.status_code == 200
    assert len(detail.json()["observations"]) == 2

    activity = client.get("/api/v1/commerce/activity/summary", headers=headers)
    assert activity.status_code == 200
    assert activity.json()["comparison_count"] == 1
    assert activity.json()["event_groups"]["watches"] == 1
    stats = client.get("/api/v1/commerce/notifications/stats", headers=headers)
    assert stats.json()["unread"] == 1
    assert stats.json()["categories"]["price"] == 1
    unread = client.get("/api/v1/commerce/notifications?category=price&unread_only=true", headers=headers)
    assert len(unread.json()) == 1
    assert client.post("/api/v1/commerce/notifications/mark-all-read?category=price", headers=headers).status_code == 204
    assert client.get("/api/v1/commerce/notifications?unread_only=true", headers=headers).json() == []


def test_cart_optimizer_persists_versions_and_records_handoff(client: TestClient) -> None:
    headers = headers_for(client, "optimizer@example.com")
    cart = client.post("/api/v1/commerce/carts", headers=headers, json={"name": "Weekly basket", "currency": "INR"}).json()
    rows = [
        ("Milk", [{"provider": "Zepto", "price": 60, "deepLink": "https://example.com/milk-z"}, {"provider": "Blinkit", "price": 55, "deepLink": "https://example.com/milk-b"}]),
        ("Bread", [{"provider": "Zepto", "price": 40, "deepLink": "https://example.com/bread-z"}, {"provider": "Blinkit", "price": 48, "deepLink": "https://example.com/bread-b"}]),
    ]
    for title, offers in rows:
        added = client.post(f"/api/v1/commerce/carts/{cart['id']}/items", headers=headers, json={"title": title, "quantity": 1, "unit_price": offers[0]["price"], "provider": offers[0]["provider"], "source_url": offers[0]["deepLink"], "metadata": {"category": "Grocery", "offers": offers}})
        assert added.status_code == 201, added.text
    optimized = client.post(f"/api/v1/commerce/carts/{cart['id']}/optimize", headers=headers, json={"objective": "balanced"})
    assert optimized.status_code == 201, optimized.text
    payload = optimized.json()
    assert payload["version"] == 1
    assert payload["result"]["financials"]["grand_total"] > 0
    assert payload["result"]["objective_applied"] == "cheapest"
    assert payload["result"]["provider_destinations"]["Zepto"].startswith("https://")
    history = client.get(f"/api/v1/commerce/carts/{cart['id']}/optimizations", headers=headers)
    assert history.status_code == 200 and len(history.json()) == 1
    handoff = client.post("/api/v1/commerce/handoffs", headers=headers, json={"provider": "Zepto", "destination_url": "https://example.com/milk-z", "expected_total": 115, "currency": "INR", "reference_id": payload["id"]})
    assert handoff.status_code == 201
    activity = client.get("/api/v1/commerce/activity?group=handoffs", headers=headers).json()
    assert activity and activity[0]["event_type"] == "handoff.opened"


def test_support_reports_and_account_control_contracts(client: TestClient) -> None:
    anonymous = client.post("/api/v1/support/reports", json={"category": "wrong_price", "subject": "Price mismatch", "description": "The provider checkout displayed a different observed total."})
    assert anonymous.status_code == 201, anonymous.text
    headers = headers_for(client, "support@example.com")
    owned = client.post("/api/v1/support/reports", headers=headers, json={"category": "wrong_product", "subject": "Different package", "description": "The package size did not match the comparison result.", "provider": "Example"})
    assert owned.status_code == 201, owned.text
    reports = client.get("/api/v1/support/reports", headers=headers)
    assert reports.status_code == 200 and [item["id"] for item in reports.json()] == [owned.json()["id"]]
    sessions = client.get("/api/v1/auth/sessions", headers=headers)
    assert sessions.status_code == 200 and sessions.json()
    exported = client.get("/api/v1/profiles/me/export", headers=headers)
    assert exported.status_code == 200
    assert exported.json()["account"]["email"] == "support@example.com"
