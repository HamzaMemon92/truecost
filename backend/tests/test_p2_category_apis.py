from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.config import settings
from app.main import app
from app.models import IngestedProviderResult, SearchSession


@pytest.fixture
def database(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'p2-test.db'}", connect_args={"check_same_thread": False})
    sessions = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield sessions
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def client(database) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_mobility_validates_coordinates_and_labels_estimates(client: TestClient) -> None:
    invalid = client.post("/api/v1/mobility/compare", json={"pickup_lat": 91, "pickup_lng": 77, "drop_lat": 19, "drop_lng": 72})
    assert invalid.status_code == 422
    same = client.post("/api/v1/mobility/compare", json={"pickup_lat": 19, "pickup_lng": 72, "drop_lat": 19, "drop_lng": 72})
    assert same.status_code == 400
    response = client.post("/api/v1/mobility/compare", json={
        "pickup_lat": 19.076, "pickup_lng": 72.8777, "drop_lat": 19.1176, "drop_lng": 72.906,
        "ride_class": "standard", "objective": "fastest",
    })
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["data_source"] == "estimated_reference_formula"
    assert payload["truecost_winner"]["eta_minutes"] == min(item["eta_minutes"] for item in payload["provider_fares"])
    assert "pickup[latitude]=19.076" in payload["provider_fares"][0]["deep_link"]
    assert "dropoff[latitude]=19.1176" in payload["provider_fares"][0]["deep_link"]


def test_travel_contract_validation_and_deterministic_provenance(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "provider_preview_enabled", True)
    missing_return = client.post("/api/v1/travel/flights/search", json={
        "origin": "DEL", "destination": "BOM", "departure_date": "2026-09-01", "passengers": 1,
        "cabin_class": "economy", "trip_type": "round_trip",
    })
    assert missing_return.status_code == 422
    request = {
        "origin": "del", "destination": "bom", "departure_date": "2026-09-01", "return_date": "2026-09-06",
        "passengers": 2, "cabin_class": "economy", "trip_type": "round_trip", "flexible_dates": True,
    }
    first = client.post("/api/v1/travel/flights/search", json=request)
    second = client.post("/api/v1/travel/flights/search", json=request)
    assert first.status_code == 200, first.text
    assert [item["total_fare"] for item in first.json()["options"]] == [item["total_fare"] for item in second.json()["options"]]
    assert all(item["data_source"] == "mock_dev_data" for item in first.json()["options"])
    assert all(item["authoritative"] is False for item in first.json()["options"])
    assert all(item["freshness_state"] == "preview" for item in first.json()["options"])
    assert "Development preview" in first.json()["disclaimer"]
    invalid_stay = client.post("/api/v1/travel/hotels/search", json={
        "destination": "Goa", "checkin_date": "2026-09-05", "checkout_date": "2026-09-04", "guests": 2, "rooms": 1,
    })
    assert invalid_stay.status_code == 422
    hotel = client.post("/api/v1/travel/hotels/search", json={
        "destination": "Goa", "checkin_date": "2026-09-05", "checkout_date": "2026-09-07", "guests": 2, "rooms": 1,
    })
    assert hotel.status_code == 200, hotel.text
    assert all(item["authoritative"] is False for item in hotel.json()["options"])
    assert all(item["freshness_state"] == "preview" for item in hotel.json()["options"])


def test_travel_inventory_fails_closed_without_verified_provider_data(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "provider_preview_enabled", False)
    response = client.post("/api/v1/travel/flights/search", json={
        "origin": "DEL", "destination": "BOM", "departure_date": "2026-09-01",
        "passengers": 1, "cabin_class": "economy", "trip_type": "one_way",
    })
    assert response.status_code == 503
    assert response.json()["error"]["message"] == "Verified flight inventory is not available"


def test_deals_are_derived_from_persisted_observations_not_client_mock_data(client: TestClient, database) -> None:
    assert client.get("/api/v1/deals").json()["deals"] == []
    with database() as db:
        session = SearchSession(query="headphones", category="Shopping")
        db.add(session)
        db.flush()
        db.add(IngestedProviderResult(
            search_session_id=session.id,
            provider="Observed Store",
            product_id="headphones-1",
            product={
                "id": "headphones-1", "name": "Noise-cancelling headphones", "category": "Shopping",
                "prices": [{"provider": "Observed Store", "price": 8000, "originalPrice": 10000, "deepLink": "https://example.test/item"}],
            },
        ))
        db.commit()
    response = client.get("/api/v1/deals?category=shopping")
    assert response.status_code == 200, response.text
    deal = response.json()["deals"][0]
    assert deal["discount_pct"] == 20
    assert deal["data_source"] == "ingested_provider_result"
    assert deal["deep_link"] == "https://example.test/item"
