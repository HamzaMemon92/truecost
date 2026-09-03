from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app
from app.models import DecisionAuditTrail
from app.services.relevance import score_exact_product


@pytest.fixture()
def client(tmp_path) -> Iterator[TestClient]:
    test_engine = create_engine(f"sqlite:///{tmp_path / 'cross_category.db'}", connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    Base.metadata.create_all(test_engine)

    def override_get_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    test_engine.dispose()


def _ingest_and_search(client: TestClient, *, provider: str, category: str, query: str, raw_data: dict) -> dict:
    ingested = client.post(
        "/api/v1/aggregator/ingest",
        json={"provider": provider, "category": category, "query": query, "raw_data": raw_data},
    )
    assert ingested.status_code == 200, ingested.text
    assert ingested.headers.get("X-Search-Session-Id")
    response = client.get(
        "/api/v1/aggregator/search",
        params={
            "q": query,
            "category": category,
            "session_id": ingested.headers["X-Search-Session-Id"],
            "exact_match": "true",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _names(body: dict, bucket: str = "primary_results") -> list[str]:
    return [item["name"] for item in body[bucket]]


def test_cross_category_exact_discovery_accepts_right_items_and_rejects_lookalikes(client: TestClient) -> None:
    scenarios = [
        {
            "label": "shopping",
            "provider": "Amazon",
            "category": "Shopping",
            "query": "Sony WH-CH520 Wireless Headphones",
            "raw_data": {"items": [
                {"name": "Sony WH-CH520 Wireless Bluetooth Headphones", "price": 4490},
                {"name": "Sony WH-XB910N Noise Cancelling Headphones", "price": 12990},
                {"name": "boAt Rockerz 450 Bluetooth Headphones", "price": 1499},
            ]},
            "expected": "Sony WH-CH520 Wireless Bluetooth Headphones",
            "rejected": ["Sony WH-XB910N Noise Cancelling Headphones", "boAt Rockerz 450 Bluetooth Headphones"],
        },
        {
            "label": "grocery",
            "provider": "Zepto",
            "category": "Grocery",
            "query": "Maggi 2 Minute Masala Noodles 70g",
            "raw_data": {
                "layout": [{
                    "widgetId": "PRODUCT_GRID",
                    "data": {"resolver": {"data": {"items": [
                        {"productResponse": {"id": "maggi-masala-70", "sellingPrice": 1400, "mrp": 1500, "product": {"name": "Maggi 2-Minute Masala Noodles", "brand": "Maggi"}, "productVariant": {"formattedPacksize": "70 g", "images": []}}},
                        {"productResponse": {"id": "maggi-atta-70", "sellingPrice": 1800, "mrp": 2000, "product": {"name": "Maggi Nutri-Licious Atta Noodles", "brand": "Maggi"}, "productVariant": {"formattedPacksize": "70 g", "images": []}}},
                    ]}}},
                }],
            },
            "expected": "Maggi 2-Minute Masala Noodles",
            "rejected": ["Maggi Nutri-Licious Atta Noodles"],
        },
        {
            "label": "pharmacy",
            "provider": "Tata 1mg",
            "category": "Pharmacy",
            "query": "Cetirizine 10mg tablet",
            "raw_data": {"items": [
                {"id": "cet-10", "name": "Cetirizine 10mg Tablet", "brand": "Generic", "selling_price": 18, "mrp": 22},
                {"id": "dolo-650", "name": "Dolo 650 Tablet", "brand": "Micro Labs", "selling_price": 34, "mrp": 36},
            ]},
            "expected": "Cetirizine 10mg Tablet",
            "rejected": ["Dolo 650 Tablet"],
        },
        {
            "label": "mobility",
            "provider": "Uber",
            "category": "Mobility",
            "query": "Uber Go ride",
            "raw_data": {"prices": [
                {"product_id": "go", "display_name": "Uber Go ride", "low_estimate": 180, "high_estimate": 240, "duration": 1500, "capacity": 4},
                {"product_id": "premier", "display_name": "Uber Premier ride", "low_estimate": 260, "high_estimate": 340, "duration": 1300, "capacity": 4},
            ]},
            "expected": "Uber Go ride",
            "rejected": ["Uber Premier ride"],
        },
        {
            "label": "finance",
            "provider": "BankBazaar",
            "category": "Finance",
            "query": "HDFC Personal Loan",
            "raw_data": {"products": [
                {"loanName": "HDFC Personal Loan", "bankName": "HDFC Bank", "interestRate": 10.75, "processingFee": "1%"},
                {"loanName": "ICICI Personal Loan", "bankName": "ICICI Bank", "interestRate": 10.9, "processingFee": "1.25%"},
            ]},
            "expected": "HDFC Personal Loan",
            "rejected": ["ICICI Personal Loan"],
        },
        {
            "label": "services",
            "provider": "Canva",
            "category": "Productivity",
            "query": "Canva Pro",
            "raw_data": {"plans": [
                {"name": "Pro", "price": 499, "features": "Brand kit and premium assets"},
                {"name": "Teams", "price": 700, "features": "Team controls"},
            ]},
            "expected": "Canva Pro",
            "rejected": ["Canva Teams"],
        },
    ]

    failures: list[str] = []
    for scenario in scenarios:
        body = _ingest_and_search(client, provider=scenario["provider"], category=scenario["category"], query=scenario["query"], raw_data=scenario["raw_data"])
        primary_names = _names(body)
        if scenario["expected"] not in primary_names:
            failures.append(f"{scenario['label']}: expected {scenario['expected']!r}, got {primary_names!r}")
        for rejected in scenario["rejected"]:
            if rejected in primary_names:
                failures.append(f"{scenario['label']}: wrongly promoted {rejected!r}")
        provider_key = scenario["provider"].casefold().replace(" ", "_")
        if scenario["provider"] == "Tata 1mg":
            provider_key = "tata1mg"
        if scenario["provider"] == "BankBazaar":
            provider_key = "bankbazaar"
        diagnostics = body["diagnostics"]["providers"]
        assert any(stats["exact_matches"] >= 1 for stats in diagnostics.values()), scenario["label"]

    assert failures == []


def test_travel_exact_identity_needs_richer_route_contract() -> None:
    """Travel currently normalizes most live rows as airline products only.

    The scorer can protect against wrong-route matches, but the connector/result
    contract must carry route/flight identity before an exact route comparison
    can be authoritative.
    """
    assert score_exact_product("Delhi to Mumbai flight", "Delhi to Mumbai non-stop flight", "MakeMyTrip") >= 0.55
    assert score_exact_product("Delhi to Mumbai flight", "Delhi to Bengaluru flight", "MakeMyTrip") < 0.55
    assert score_exact_product("Delhi to Mumbai flight", "IndiGo", "MakeMyTrip") < 0.55


def test_exact_discovery_persists_idempotent_decision_audit(client: TestClient, tmp_path) -> None:
    ingested = client.post(
        "/api/v1/aggregator/ingest",
        json={
            "provider": "Amazon",
            "category": "Shopping",
            "query": "Noise Airwave Max 6 Bluetooth",
            "raw_data": {"items": [
                {"id": "noise-max-6", "name": "Noise Airwave Max 6 Bluetooth Headphones", "price": 1299},
                {"id": "noise-max-2", "name": "Noise Airwave Max 2 Bluetooth Headphones", "price": 599},
            ]},
        },
    )
    assert ingested.status_code == 200, ingested.text
    session_id = ingested.headers["X-Search-Session-Id"]
    params = {"q": "Noise Airwave Max 6 Bluetooth", "category": "Shopping", "session_id": session_id, "exact_match": "true"}

    first = client.get("/api/v1/aggregator/search", params=params)
    second = client.get("/api/v1/aggregator/search", params=params)
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["discovery_report"]["exact_results"]
    assert all("Max 2" not in item["name"] for item in first.json()["discovery_report"]["exact_results"])

    # Open a new DB session through the app override's SQLite file by asking the
    # API to create/read the audit indirectly, then verify the artifact exists.
    # The client fixture's engine is private, so use the app's override generator.
    override = app.dependency_overrides[get_db]
    db_generator = override()
    db = next(db_generator)
    try:
        audits = db.query(DecisionAuditTrail).filter(DecisionAuditTrail.search_session_id == session_id).all()
        assert len(audits) == 1
        audit = audits[0]
        assert audit.selected_identity["identity_fingerprint"]
        assert isinstance(audit.selected_identity.get("identity_factors") or audit.selected_identity.get("attributes"), dict)
        assert audit.exact_results
        assert audit.rejected_results
        assert audit.final_decision["confidence"] == "high"
    finally:
        db.close()

    audit_response = client.get(f"/api/v1/aggregator/decision-audits/{session_id}")
    assert audit_response.status_code == 200, audit_response.text
    payload = audit_response.json()
    assert payload["search_session_id"] == session_id
    assert len(payload["audits"]) == 1
    assert payload["audits"][0]["exact_results"]
    assert payload["audits"][0]["rejected_results"]
