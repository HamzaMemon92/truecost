from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import IngestedProviderResult, SearchSession
from app.schemas.product import ProviderPrice, TrueCostProduct


@pytest.fixture()
def client_with_factory() -> Iterator[tuple[TestClient, sessionmaker]]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, factory
    app.dependency_overrides.clear()
    engine.dispose()


def _product(provider: str, name: str, price: float) -> TrueCostProduct:
    return TrueCostProduct(
        id=f"{provider}-amul-gold-500ml",
        name=name,
        brand="Amul",
        category="Grocery",
        weight_volume="500 ml",
        prices=[ProviderPrice(provider=provider.title(), price=price)],
    )


def test_exact_grocery_search_ranks_requested_amul_gold_before_taaza_and_compares_providers(client_with_factory) -> None:
    client, factory = client_with_factory
    session = SearchSession(query="Milk Amul Gold 500 ml pouch", category="Grocery")
    gold_products = [
        ("blinkit", "Amul Gold Full Cream Fresh Milk | Pouch", 36),
        ("zepto", "Amul Gold Full Cream Milk Pouch", 35),
        ("swiggy", "Amul Gold Pasteurised Full Cream Milk", 36),
        ("bigbasket", "Gold Full Cream Milk", 32),
    ]
    with factory() as db:
        db.add(session)
        db.flush()
        for provider, name, price in gold_products:
            product = _product(provider, name, price)
            db.add(IngestedProviderResult(
                search_session_id=session.id,
                provider=provider,
                product_id=product.id,
                product=product.model_dump(by_alias=True),
                ingestion_key=f"{provider}-gold",
            ))
        taaza = TrueCostProduct(
            id="bigbasket-amul-taaza-500ml",
            name="Taaza Milk",
            brand="Amul",
            category="Grocery",
            weight_volume="500 ml",
            prices=[ProviderPrice(provider="BigBasket", price=27)],
        )
        db.add(IngestedProviderResult(
            search_session_id=session.id,
            provider="bigbasket",
            product_id=taaza.id,
            product=taaza.model_dump(by_alias=True),
            ingestion_key="bigbasket-taaza",
        ))
        for provider, name, weight, price in [
            ("zepto", "Amul Lactose Free Milk (Tetra Pack)", "250 ml", 17),
            ("swiggy", "Amul Shrikhand Elaichi", "500 g", 125),
            ("swiggy", "Amul Processed Cheese Block", "200 g", 129),
        ]:
            decoy = TrueCostProduct(
                id=f"{provider}-{name}".replace(" ", "-").casefold(),
                name=name,
                brand="Amul",
                category="Grocery",
                weight_volume=weight,
                prices=[ProviderPrice(provider=provider.title(), price=price)],
            )
            db.add(IngestedProviderResult(
                search_session_id=session.id,
                provider=provider,
                product_id=decoy.id,
                product=decoy.model_dump(by_alias=True),
                ingestion_key=f"{provider}-{name}",
            ))
        db.commit()
        session_id = session.id

    response = client.get(
        "/api/v1/aggregator/search",
        params={
            "q": "Milk Amul Gold 500 ml pouch",
            "category": "Grocery",
            "session_id": session_id,
            "exact_match": "true",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["search_intelligence"]["show_correction_banner"] is False
    assert "boult" not in body["corrected_query"].casefold()
    primary_names = [item["name"] for item in body["primary_results"]]
    assert primary_names
    assert "gold" in primary_names[0].casefold()
    assert all("taaza" not in name.casefold() for name in primary_names)
    assert all("lactose" not in name.casefold() for name in primary_names)
    assert all("shrikhand" not in name.casefold() for name in primary_names)
    assert all("cheese" not in name.casefold() for name in primary_names)
    offer_providers = {
        price["provider"].casefold()
        for result in body["primary_results"]
        for price in result["prices"]
    }
    assert {"blinkit", "zepto", "swiggy", "bigbasket"}.issubset(offer_providers)


def test_provider_ingests_with_client_session_id_share_one_search_session(client_with_factory) -> None:
    client, factory = client_with_factory
    session_id = "11111111-2222-4333-8444-555555555555"

    blinkit = client.post(
        "/api/v1/aggregator/ingest",
        json={
            "provider": "Blinkit",
            "query": "Milk Amul Gold 500 ml pouch",
            "category": "Grocery",
            "search_session_id": session_id,
            "raw_data": {
                "products": [{
                    "id": "blinkit-gold",
                    "nav_id": "123456",
                    "name": "Amul Gold Full Cream Fresh Milk | Pouch",
                    "brand": "Amul",
                    "unit": "500 ml",
                    "sp": 36,
                    "mrp": 36,
                }]
            },
        },
    )
    bigbasket = client.post(
        "/api/v1/aggregator/ingest",
        json={
            "provider": "BigBasket",
            "query": "Milk Amul Gold 500 ml pouch",
            "category": "Grocery",
            "search_session_id": session_id,
            "raw_data": {
                "products": [{
                    "id": "bb-gold",
                    "desc": "Gold Full Cream Milk",
                    "brand": {"name": "Amul"},
                    "w": "500 ml",
                    "aps": {"sp": 32, "mrp": 32},
                }]
            },
        },
    )

    assert blinkit.status_code == 200, blinkit.text
    assert bigbasket.status_code == 200, bigbasket.text
    assert blinkit.headers["X-Search-Session-Id"] == session_id
    assert bigbasket.headers["X-Search-Session-Id"] == session_id

    with factory() as db:
        sessions = db.query(SearchSession).all()
        rows = db.query(IngestedProviderResult).all()
    assert [session.id for session in sessions] == [session_id]
    assert {row.provider for row in rows} == {"blinkit", "bigbasket"}
