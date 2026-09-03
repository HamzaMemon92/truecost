from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path) -> Iterator[TestClient]:
    engine = create_engine(f"sqlite:///{tmp_path / 'elite-acceptance.db'}", connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def _ingest(client: TestClient, *, provider: str, category: str, query: str, raw_data: dict) -> str:
    response = client.post("/api/v1/aggregator/ingest", json={"provider": provider, "category": category, "query": query, "raw_data": raw_data})
    assert response.status_code == 200, response.text
    assert response.headers.get("X-Search-Session-Id"), f"{provider}/{category}/{query} did not create a session"
    return response.headers["X-Search-Session-Id"]


def _search(client: TestClient, *, session_id: str, category: str, query: str) -> dict:
    response = client.get("/api/v1/aggregator/search", params={"session_id": session_id, "category": category, "q": query, "exact_match": "true"})
    assert response.status_code == 200, response.text
    return response.json()


def _assert_exact_matrix(client: TestClient, scenarios: list[dict]) -> list[dict]:
    report_rows: list[dict] = []
    for scenario in scenarios:
        session_id = _ingest(client, provider=scenario["provider"], category=scenario["category"], query=scenario["query"], raw_data=scenario["raw_data"])
        body = _search(client, session_id=session_id, category=scenario["category"], query=scenario["query"])
        discovery = body["discovery_report"]
        exact_names = [item["name"] for item in discovery["exact_results"]]
        related_names = [item["name"] for item in discovery["related_results"]]
        rejected_names = [item["name"] for item in discovery["rejected_results"]]
        assert scenario["expected"] in exact_names, f"{scenario['query']} expected exact {scenario['expected']!r}, got {exact_names!r}"
        for forbidden in scenario.get("forbidden", []):
            assert forbidden not in exact_names, f"{scenario['query']} wrongly compared lookalike {forbidden!r}"
        report_rows.append({
            "category": scenario["category"],
            "query": scenario["query"],
            "provider": scenario["provider"],
            "exact": len(exact_names),
            "related": len(related_names),
            "rejected": len(rejected_names),
            "best": discovery["best_observed"]["offer"]["price"] if discovery.get("best_observed") else None,
        })
    return report_rows


def test_product_identity_acceptance_matrix_5_categories_20_products(client: TestClient) -> None:
    scenarios = [
        # Shopping
        {"provider": "Amazon", "category": "Shopping", "query": "Noise Airwave Max 6 Bluetooth", "expected": "Noise Airwave Max 6 Bluetooth Headphones", "forbidden": ["Noise Airwave Max 2 Bluetooth Headphones", "TechFusion BT MAX Neckband"], "raw_data": {"items": [
            {"id": "noise-max6", "name": "Noise Airwave Max 6 Bluetooth Headphones", "price": 1299},
            {"id": "noise-max2", "name": "Noise Airwave Max 2 Bluetooth Headphones", "price": 599},
            {"id": "techfusion-neck", "name": "TechFusion BT MAX Neckband", "price": 328},
        ]}},
        {"provider": "Amazon", "category": "Shopping", "query": "Sony WH-CH520 Wireless Headphones", "expected": "Sony WH-CH520 Wireless Bluetooth Headphones", "forbidden": ["Sony WH-XB910N Noise Cancelling Headphones"], "raw_data": {"items": [
            {"id": "sony-ch520", "name": "Sony WH-CH520 Wireless Bluetooth Headphones", "price": 4490},
            {"id": "sony-xb910", "name": "Sony WH-XB910N Noise Cancelling Headphones", "price": 12990},
        ]}},
        {"provider": "Amazon", "category": "Shopping", "query": "iPhone 15 128GB Blue", "expected": "Apple iPhone 15 128GB Blue", "forbidden": ["Apple iPhone 15 256GB Blue", "Apple iPhone 14 128GB Blue"], "raw_data": {"items": [
            {"id": "iphone15-128-blue", "name": "Apple iPhone 15 128GB Blue", "price": 69999},
            {"id": "iphone15-256-blue", "name": "Apple iPhone 15 256GB Blue", "price": 79999},
            {"id": "iphone14-128-blue", "name": "Apple iPhone 14 128GB Blue", "price": 58999},
        ]}},
        {"provider": "Amazon", "category": "Shopping", "query": "boAt Airdopes 141 ANC", "expected": "boAt Airdopes 141 ANC TWS Earbuds", "forbidden": ["boAt Rockerz 255 Pro Neckband"], "raw_data": {"items": [
            {"id": "boat-141-anc", "name": "boAt Airdopes 141 ANC TWS Earbuds", "price": 1499},
            {"id": "boat-rockerz", "name": "boAt Rockerz 255 Pro Neckband", "price": 999},
        ]}},
        # Grocery
        {"provider": "Zepto", "category": "Grocery", "query": "Maggi 2 Minute Masala Noodles 70g", "expected": "Maggi 2-Minute Masala Noodles", "forbidden": ["Maggi Nutri-Licious Atta Noodles"], "raw_data": _zepto_items([
            ("maggi-masala-70", "Maggi 2-Minute Masala Noodles", "Maggi", "70 g", 1400),
            ("maggi-atta-70", "Maggi Nutri-Licious Atta Noodles", "Maggi", "70 g", 1800),
        ])},
        {"provider": "Zepto", "category": "Grocery", "query": "Amul Taaza Milk 1L", "expected": "Amul Taaza Toned Milk", "forbidden": ["Amul Gold Full Cream Milk"], "raw_data": _zepto_items([
            ("amul-taaza-1l", "Amul Taaza Toned Milk", "Amul", "1 L", 5600),
            ("amul-gold-1l", "Amul Gold Full Cream Milk", "Amul", "1 L", 6800),
        ])},
        {"provider": "Zepto", "category": "Grocery", "query": "Tata Salt 1kg", "expected": "Tata Salt Iodized", "forbidden": ["Tata Salt Lite Low Sodium"], "raw_data": _zepto_items([
            ("tata-salt-1kg", "Tata Salt Iodized", "Tata", "1 kg", 2800),
            ("tata-salt-lite-1kg", "Tata Salt Lite Low Sodium", "Tata", "1 kg", 4200),
        ])},
        {"provider": "Zepto", "category": "Grocery", "query": "Britannia Good Day Cashew 200g", "expected": "Britannia Good Day Cashew Cookies", "forbidden": ["Britannia Good Day Butter Cookies"], "raw_data": _zepto_items([
            ("good-day-cashew-200", "Britannia Good Day Cashew Cookies", "Britannia", "200 g", 4500),
            ("good-day-butter-200", "Britannia Good Day Butter Cookies", "Britannia", "200 g", 3500),
        ])},
        # Pharmacy
        {"provider": "Tata 1mg", "category": "Pharmacy", "query": "Dolo 650 Tablet", "expected": "Dolo 650 Tablet", "forbidden": ["Paracetamol 500mg Tablet"], "raw_data": {"items": [
            {"id": "dolo-650", "name": "Dolo 650 Tablet", "brand": "Micro Labs", "selling_price": 34, "mrp": 36},
            {"id": "para-500", "name": "Paracetamol 500mg Tablet", "brand": "Generic", "selling_price": 12, "mrp": 15},
        ]}},
        {"provider": "Tata 1mg", "category": "Pharmacy", "query": "Cetirizine 10mg Tablet", "expected": "Cetirizine 10mg Tablet", "forbidden": ["Cetirizine Syrup 5mg"], "raw_data": {"items": [
            {"id": "cet-10-tab", "name": "Cetirizine 10mg Tablet", "brand": "Generic", "selling_price": 18, "mrp": 22},
            {"id": "cet-syrup", "name": "Cetirizine Syrup 5mg", "brand": "Generic", "selling_price": 42, "mrp": 50},
        ]}},
        {"provider": "Tata 1mg", "category": "Pharmacy", "query": "Volini Spray 100g", "expected": "Volini Pain Relief Spray", "forbidden": ["Volini Gel 30g"], "raw_data": {"items": [
            {"id": "volini-spray-100", "name": "Volini Pain Relief Spray", "brand": "Volini", "pack_size": "100 g", "selling_price": 260, "mrp": 299},
            {"id": "volini-gel-30", "name": "Volini Gel 30g", "brand": "Volini", "selling_price": 112, "mrp": 130},
        ]}},
        {"provider": "Tata 1mg", "category": "Pharmacy", "query": "Shelcal 500 Tablet", "expected": "Shelcal 500 Tablet", "forbidden": ["Shelcal XT Tablet"], "raw_data": {"items": [
            {"id": "shelcal-500", "name": "Shelcal 500 Tablet", "brand": "Torrent", "selling_price": 118, "mrp": 130},
            {"id": "shelcal-xt", "name": "Shelcal XT Tablet", "brand": "Torrent", "selling_price": 210, "mrp": 245},
        ]}},
        # Finance
        {"provider": "BankBazaar", "category": "Finance", "query": "HDFC Personal Loan", "expected": "HDFC Personal Loan", "forbidden": ["ICICI Personal Loan"], "raw_data": {"products": [
            {"loanName": "HDFC Personal Loan", "bankName": "HDFC Bank", "interestRate": 10.75, "processingFee": "1%"},
            {"loanName": "ICICI Personal Loan", "bankName": "ICICI Bank", "interestRate": 10.9, "processingFee": "1.25%"},
        ]}},
        {"provider": "BankBazaar", "category": "Finance", "query": "SBI Cashback Credit Card", "expected": "SBI Cashback Credit Card", "forbidden": ["HDFC Millennia Credit Card"], "raw_data": {"products": [
            {"cardName": "SBI Cashback Credit Card", "bankName": "SBI", "annualFee": 999, "benefits": "Cashback"},
            {"cardName": "HDFC Millennia Credit Card", "bankName": "HDFC Bank", "annualFee": 1000, "benefits": "Cashpoints"},
        ]}},
        {"provider": "BankBazaar", "category": "Finance", "query": "Axis Bank Neo Credit Card", "expected": "Axis Bank Neo Credit Card", "forbidden": ["Axis Bank Ace Credit Card"], "raw_data": {"products": [
            {"cardName": "Axis Bank Neo Credit Card", "bankName": "Axis Bank", "annualFee": 250, "benefits": "Shopping offers"},
            {"cardName": "Axis Bank Ace Credit Card", "bankName": "Axis Bank", "annualFee": 499, "benefits": "Cashback"},
        ]}},
        {"provider": "BankBazaar", "category": "Finance", "query": "ICICI Home Loan", "expected": "ICICI Home Loan", "forbidden": ["SBI Home Loan"], "raw_data": {"products": [
            {"loanName": "ICICI Home Loan", "bankName": "ICICI Bank", "interestRate": 8.75, "processingFee": "0.5%"},
            {"loanName": "SBI Home Loan", "bankName": "SBI", "interestRate": 8.5, "processingFee": "0.35%"},
        ]}},
        # Services/Productivity
        {"provider": "Canva", "category": "Productivity", "query": "Canva Pro", "expected": "Canva Pro", "forbidden": ["Canva Teams"], "raw_data": {"plans": [
            {"name": "Pro", "price": 499, "features": "Brand kit and premium assets"},
            {"name": "Teams", "price": 700, "features": "Team controls"},
        ]}},
        {"provider": "Notion", "category": "Productivity", "query": "Notion Plus", "expected": "Notion Plus", "forbidden": ["Notion Business"], "raw_data": {"plans": [
            {"name": "Plus", "price": 830, "features": "Unlimited blocks"},
            {"name": "Business", "price": 1660, "features": "SAML and private teamspaces"},
        ]}},
        {"provider": "Slack", "category": "Productivity", "query": "Slack Pro", "expected": "Slack Pro", "forbidden": ["Slack Business Plus"], "raw_data": {"plans": [
            {"name": "Pro", "price": 725, "features": "Unlimited message history"},
            {"name": "Business Plus", "price": 1320, "features": "Advanced compliance"},
        ]}},
        {"provider": "Figma", "category": "Productivity", "query": "Figma Professional", "expected": "Figma Professional", "forbidden": ["Figma Organization"], "raw_data": {"plans": [
            {"name": "Professional", "price": 1000, "features": "Team libraries"},
            {"name": "Organization", "price": 3750, "features": "Centralized admin"},
        ]}},
    ]
    rows = _assert_exact_matrix(client, scenarios)
    print("\nELITE ACCEPTANCE MATRIX")
    for row in rows:
        print(f"{row['category']:12} | {row['provider']:10} | exact={row['exact']} related={row['related']} rejected={row['rejected']} best={row['best']} | {row['query']}")
    assert len(rows) == 20


def test_decision_categories_4_plus_flows_are_honest_and_deterministic(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    mobility_requests = [
        {"pickup_lat": 19.076, "pickup_lng": 72.8777, "drop_lat": 19.1176, "drop_lng": 72.906, "ride_class": "standard", "objective": "cheapest"},
        {"pickup_lat": 28.6139, "pickup_lng": 77.209, "drop_lat": 28.5562, "drop_lng": 77.1, "ride_class": "standard", "objective": "fastest"},
        {"pickup_lat": 12.9716, "pickup_lng": 77.5946, "drop_lat": 13.0358, "drop_lng": 77.597, "ride_class": "premium", "objective": "comfort"},
        {"pickup_lat": 18.5204, "pickup_lng": 73.8567, "drop_lat": 18.6298, "drop_lng": 73.7997, "ride_class": "auto", "objective": "cheapest"},
    ]
    for request in mobility_requests:
        response = client.post("/api/v1/mobility/compare", json=request)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["data_source"] == "estimated_reference_formula"
        assert payload["truecost_winner"]["provider"] in {item["provider"] for item in payload["provider_fares"]}
    monkeypatch.setattr(settings, "provider_preview_enabled", True)
    flight = client.post("/api/v1/travel/flights/search", json={"origin": "DEL", "destination": "BOM", "departure_date": "2026-09-01", "passengers": 1, "cabin_class": "economy", "trip_type": "one_way"})
    hotel = client.post("/api/v1/travel/hotels/search", json={"destination": "Goa", "checkin_date": "2026-09-05", "checkout_date": "2026-09-07", "guests": 2, "rooms": 1})
    assert flight.status_code == 200, flight.text
    assert hotel.status_code == 200, hotel.text
    assert all(item["authoritative"] is False and item["freshness_state"] == "preview" for item in flight.json()["options"])
    assert all(item["authoritative"] is False and item["freshness_state"] == "preview" for item in hotel.json()["options"])


def _zepto_items(items: list[tuple[str, str, str, str, int]]) -> dict:
    return {
        "layout": [{
            "widgetId": "PRODUCT_GRID",
            "data": {"resolver": {"data": {"items": [
                {"productResponse": {
                    "id": item_id,
                    "sellingPrice": price,
                    "mrp": int(price * 1.1),
                    "product": {"name": name, "brand": brand},
                    "productVariant": {"formattedPacksize": pack, "images": []},
                }}
                for item_id, name, brand, pack, price in items
            ]}}},
        }],
    }
