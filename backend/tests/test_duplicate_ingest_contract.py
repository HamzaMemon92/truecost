from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import IngestedProviderResult


@pytest.fixture()
def ingestion() -> Iterator[tuple[TestClient, sessionmaker]]:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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


def test_duplicate_provider_api_and_dom_payloads_should_collapse_to_one_product(ingestion) -> None:
    client, factory = ingestion
    api_payload = {
        "provider": "Blinkit",
        "query": "Saffola Muesli Choco Crunch",
        "category": "Grocery",
        "raw_data": {
            "cart_item": {
                "product_id": "123456",
                "product_name": "Saffola Muesli Choco Crunch with Flavour Pops",
                "display_name": "Saffola Muesli Choco Crunch with Flavour Pops",
                "brand": "Saffola",
                "unit": "700 g",
                "price": 195,
                "mrp": 445,
            }
        },
    }
    first = client.post("/api/v1/aggregator/ingest", json=api_payload)
    assert first.status_code == 200, first.text

    dom_payload = {
        **api_payload,
        "search_session_id": first.headers["X-Search-Session-Id"],
        "raw_data": {
            "products": [
                {
                    "id": "123456",
                    "nav_id": "123456",
                    "name": "Saffola Muesli Choco Crunch with Flavour Pops",
                    "brand": "Saffola",
                    "unit": "700 g",
                    "sp": 195,
                    "mrp": 445,
                }
            ]
        },
    }
    second = client.post("/api/v1/aggregator/ingest", json=dom_payload)
    assert second.status_code == 200, second.text

    with factory() as db:
        assert db.scalar(select(func.count()).select_from(IngestedProviderResult)) == 1
