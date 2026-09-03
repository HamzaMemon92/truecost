from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app
from app.models import IngestedProviderResult, SearchSession


@pytest.fixture()
def ingestion(tmp_path) -> Iterator[tuple[TestClient, sessionmaker]]:
    test_engine = create_engine(f"sqlite:///{tmp_path / 'ingestion.db'}", connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    Base.metadata.create_all(test_engine)

    def override_get_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, factory
    app.dependency_overrides.clear()
    test_engine.dispose()


def test_ingest_is_owned_persistent_and_safe_to_retry(ingestion) -> None:
    client, factory = ingestion
    tokens = client.post("/api/v1/auth/register", json={"email": "ingest@example.com", "password": "a-strong-password"}).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    payload = {"provider": "Amazon", "query": "headphones", "category": "Shopping", "raw_data": {"items": [{"name": "Headphones", "price": 1000}]}}
    first = client.post("/api/v1/aggregator/ingest", headers=headers, json=payload)
    assert first.status_code == 200, first.text
    session_id = first.headers["X-Search-Session-Id"]
    payload["search_session_id"] = session_id
    second = client.post("/api/v1/aggregator/ingest", headers=headers, json=payload)
    assert second.status_code == 200, second.text

    with factory() as db:
        session = db.get(SearchSession, session_id)
        assert session is not None and session.user_id == tokens["user_id"]
        assert db.scalar(select(func.count()).select_from(IngestedProviderResult)) == 1
        row = db.scalar(select(IngestedProviderResult))
        assert row is not None and row.provider == "amazon" and len(row.ingestion_key) == 64


def test_unknown_ingest_provider_uses_error_envelope(ingestion) -> None:
    client, _ = ingestion
    response = client.post("/api/v1/aggregator/ingest", json={"provider": "not-a-provider", "query": "x", "raw_data": {}})
    assert response.status_code == 400
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_suggestions_use_only_persisted_canonical_products(ingestion) -> None:
    client, _ = ingestion
    payload = {
        "provider": "Amazon",
        "query": "amul",
        "category": "Grocery",
        "raw_data": {"items": [{"name": "Amul Taaza Milk 1L", "brand": "Amul", "price": 72, "image": "https://images.example/amul-taaza.jpg"}]},
    }
    assert client.get("/api/v1/aggregator/suggestions", params={"q": "amul", "category": "Grocery"}).json() == []
    ingested = client.post("/api/v1/aggregator/ingest", json=payload)
    assert ingested.status_code == 200, ingested.text

    response = client.get("/api/v1/aggregator/suggestions", params={"q": "taaza", "category": "Grocery"})
    assert response.status_code == 200
    suggestions = response.json()
    assert len(suggestions) == 1
    assert suggestions[0]["query"] == "Amul Taaza Milk 1L"
    assert suggestions[0]["kind"] == "observed_product"
    assert suggestions[0]["provider_count"] == 1

    assert client.get("/api/v1/aggregator/suggestions", params={"q": "amul", "category": "Shopping"}).json() == []


def test_search_promotes_exact_model_and_uses_category_provider_scope(ingestion) -> None:
    client, _ = ingestion
    payload = {
        "provider": "Meesho",
        "query": "noise headphones",
        "category": "Shopping",
        "raw_data": {"items": [
            {"name": "Bluetooth Headphones & Earphones", "brand": "Meesho", "price": 306},
            {"name": "Noise Airwave Max 4 Wireless Headphones", "brand": "Noise", "price": 1799},
        ]},
    }
    ingested = client.post("/api/v1/aggregator/ingest", json=payload)
    assert ingested.status_code == 200, ingested.text
    session_id = ingested.headers["X-Search-Session-Id"]

    broad = client.get("/api/v1/aggregator/search", params={"q": "noise headphones", "category": "Shopping", "session_id": session_id})
    assert broad.status_code == 200
    broad_body = broad.json()
    names = [item["name"] for item in broad_body["primary_results"]]
    assert "Noise Airwave Max 4 Wireless Headphones" in names
    assert "zepto" not in broad_body["providers_pending"]
    assert set(broad_body["providers_pending"]).issubset({"amazon", "flipkart", "meesho", "myntra"})

    focused = client.get("/api/v1/aggregator/search", params={"q": "Noise Airwave Max 4", "category": "Shopping", "session_id": session_id})
    assert focused.status_code == 200
    focused_body = focused.json()
    assert focused_body["primary_results"][0]["name"] == "Noise Airwave Max 4 Wireless Headphones"
    assert focused_body["primary_results"][0]["matchTier"] == "primary"
    assert focused_body["primary_results"][0]["matchScore"] >= 0.55


def test_exact_match_search_does_not_compare_different_headphone_models(ingestion) -> None:
    client, _ = ingestion
    payload = {
        "provider": "Amazon",
        "query": "Noise Airwave Max 6 Bluetooth",
        "category": "Shopping",
        "raw_data": {"items": [
            {"name": "TechFusion BT MAX Neckband", "brand": "TechFusion", "price": 328},
            {"name": "Noise Airwave Max 2 50H Battery Bluetooth Headphones", "brand": "Noise", "price": 2999},
            {"name": "Noise Airwave Max 6 Bluetooth", "brand": "Noise", "price": 1899},
        ]},
    }
    ingested = client.post("/api/v1/aggregator/ingest", json=payload)
    assert ingested.status_code == 200, ingested.text
    session_id = ingested.headers["X-Search-Session-Id"]

    response = client.get(
        "/api/v1/aggregator/search",
        params={"q": "Noise Airwave Max 6 Bluetooth", "category": "Shopping", "session_id": session_id, "exact_match": "true"},
    )
    assert response.status_code == 200
    body = response.json()
    primary_names = [item["name"] for item in body["primary_results"]]
    related_names = [item["name"] for item in body["recommendations"]]

    assert primary_names == ["Noise Airwave Max 6 Bluetooth"]
    assert "TechFusion BT MAX Neckband" not in primary_names
    assert "Noise Airwave Max 2 50H Battery Bluetooth Headphones" not in primary_names
    assert "TechFusion BT MAX Neckband" not in related_names
    assert body["diagnostics"]["providers"]["amazon"]["observed"] == 3
    assert body["diagnostics"]["providers"]["amazon"]["exact_matches"] == 1
    assert body["diagnostics"]["providers"]["amazon"]["rejected"] >= 2
    assert body["discovery_report"]["selected_identity"]["identity_fingerprint"]
    assert body["discovery_report"]["exact_results"][0]["identity"]["match_tier"] in {"exact", "probable"}
    assert body["discovery_report"]["best_observed"]["offer"]["price"] == 1899
    assert body["discovery_report"]["decision_explanation"]


def test_exact_match_explains_provider_response_without_exact_sku(ingestion) -> None:
    client, _ = ingestion
    payload = {
        "provider": "Flipkart",
        "query": "Noise Airwave Max 6 Bluetooth",
        "category": "Shopping",
        "provider_query": "Noise Airwave Max 6",
        "exact_discovery_attempt": 1,
        "raw_data": {"items": [
            {"name": "TechFusion BT MAX Neckband", "brand": "TechFusion", "sellingPrice": {"value": 328}, "price": {"value": 328}},
            {"name": "abhi A4 Airbuds TWS Max", "brand": "abhi", "sellingPrice": {"value": 336}, "price": {"value": 336}},
            {"name": "DUJE Wireless Aerobeats", "brand": "DUJE", "sellingPrice": {"value": 489}, "price": {"value": 489}},
        ]},
    }
    ingested = client.post("/api/v1/aggregator/ingest", json=payload)
    assert ingested.status_code == 200, ingested.text

    response = client.get(
        "/api/v1/aggregator/search",
        params={
            "q": "Noise Airwave Max 6 Bluetooth",
            "category": "Shopping",
            "session_id": ingested.headers["X-Search-Session-Id"],
            "exact_match": "true",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["primary_results"] == []
    assert body["diagnostics"]["providers"]["flipkart"]["observed"] == 3
    assert body["diagnostics"]["providers"]["flipkart"]["exact_matches"] == 0
    assert body["diagnostics"]["providers"]["flipkart"]["rejected"] == 3
    assert body["diagnostics"]["providers"]["flipkart"]["best_rejected"][0]["reason"]
    assert body["discovery_report"]["exact_results"] == []
    assert len(body["discovery_report"]["rejected_results"]) == 3


def test_flipkart_selling_price_payload_is_parsed_for_exact_discovery(ingestion) -> None:
    client, _ = ingestion
    payload = {
        "provider": "Flipkart",
        "query": "Noise Airwave Max 6 Bluetooth",
        "category": "Shopping",
        "raw_data": {"items": [
            {"name": "Noise Airwave Max 6 Bluetooth", "brand": "Noise", "sellingPrice": {"value": 1599}},
        ]},
    }
    ingested = client.post("/api/v1/aggregator/ingest", json=payload)
    assert ingested.status_code == 200, ingested.text
    assert ingested.json()[0]["prices"][0]["price"] == 1599

    response = client.get(
        "/api/v1/aggregator/search",
        params={
            "q": "Noise Airwave Max 6 Bluetooth",
            "category": "Shopping",
            "session_id": ingested.headers["X-Search-Session-Id"],
            "exact_match": "true",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["primary_results"][0]["name"] == "Noise Airwave Max 6 Bluetooth"
    assert body["diagnostics"]["providers"]["flipkart"]["exact_matches"] == 1

