from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.api.endpoints.aggregator import _balance_discovery_results, _promote_discovery_provider_coverage
from app.main import app


@pytest.fixture()
def client() -> Iterator[TestClient]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def test_broad_grocery_query_surfaces_discovery_results(client: TestClient) -> None:
    ingest = client.post(
        "/api/v1/aggregator/ingest",
        json={
            "provider": "Blinkit",
            "query": "Room freshener",
            "category": "Grocery",
            "raw_data": {
                "products": [
                    {
                        "id": "rf-1",
                        "nav_id": "123456",
                        "name": "Godrej Aer Air Freshener Spray",
                        "brand": "Godrej",
                        "unit": "220 ml",
                        "sp": 149,
                        "mrp": 179,
                    }
                ]
            },
        },
    )
    assert ingest.status_code == 200, ingest.text

    result = client.get(
        "/api/v1/aggregator/search",
        params={
            "q": "Room freshener",
            "category": "Grocery",
            "session_id": ingest.headers["X-Search-Session-Id"],
            "exact_match": "true",
        },
    )
    assert result.status_code == 200, result.text
    body = result.json()

    assert body["diagnostics"]["discovery_query"] is True
    assert body["primary_results"]
    assert "freshener" in body["primary_results"][0]["name"].casefold()


def test_broad_discovery_results_are_provider_balanced_after_true_comparisons() -> None:
    products = [
        {
            "id": "same-product",
            "name": "Godrej Aer Room Freshener Spray",
            "category": "Grocery",
            "prices": [
                {"provider": "Blinkit", "price": 149},
                {"provider": "Zepto", "price": 151},
            ],
        }
    ]
    products.extend(
        {
            "id": f"bb-{index}",
            "name": f"BigBasket Room Freshener {index}",
            "category": "Grocery",
            "prices": [{"provider": "BigBasket", "price": 180 + index}],
        }
        for index in range(5)
    )
    products.extend(
        {
            "id": f"zepto-{index}",
            "name": f"Zepto Room Freshener {index}",
            "category": "Grocery",
            "prices": [{"provider": "Zepto", "price": 160 + index}],
        }
        for index in range(3)
    )
    products.extend(
        {
            "id": f"swiggy-{index}",
            "name": f"Swiggy Room Freshener {index}",
            "category": "Grocery",
            "prices": [{"provider": "Swiggy Instamart", "price": 170 + index}],
        }
        for index in range(2)
    )

    balanced = _balance_discovery_results(products)
    first_screen_providers = [item["prices"][0]["provider"] for item in balanced[:7]]

    assert balanced[0]["id"] == "same-product"
    assert first_screen_providers == [
        "Blinkit",
        "BigBasket",
        "Zepto",
        "Swiggy Instamart",
        "BigBasket",
        "Zepto",
        "Swiggy Instamart",
    ]


def test_broad_discovery_promotes_relevant_missing_provider_coverage() -> None:
    primary = [
        {
            "id": "bb-1",
            "name": "BigBasket Room Freshener",
            "brand": "Godrej",
            "weightVolume": "220 ml",
            "matchScore": 0.72,
            "prices": [{"provider": "BigBasket", "price": 179}],
        }
    ]
    secondary = [
        {
            "id": f"sw-{index}",
            "name": f"Swiggy Room Freshener {index}",
            "brand": "Godrej",
            "weightVolume": "220 ml",
            "matchTier": "related",
            "matchScore": 0.45,
            "queryRelevance": "EXACT",
            "prices": [{"provider": "Swiggy Instamart", "price": 189 + index}],
        }
        for index in range(4)
    ]
    secondary.append({
        "id": "snack-1",
        "name": "Potato Chips",
        "brand": "Snack",
        "matchTier": "related",
        "matchScore": 0.6,
        "queryRelevance": "COMPLEMENT",
        "prices": [{"provider": "Zepto", "price": 50}],
    })

    promoted_primary, remaining = _promote_discovery_provider_coverage(primary, secondary)

    providers = [item["prices"][0]["provider"] for item in promoted_primary]
    assert providers == ["BigBasket", "Swiggy Instamart", "Swiggy Instamart", "Swiggy Instamart"]
    assert "snack-1" in {item["id"] for item in remaining}
