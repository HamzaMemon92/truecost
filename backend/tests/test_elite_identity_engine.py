from app.schemas.product import ProviderPrice, TrueCostProduct
from app.services.product_identity import identity_engine


def _product(name: str, brand: str, provider: str = "Amazon", category: str = "Shopping") -> TrueCostProduct:
    return TrueCostProduct(
        id=f"{provider}-{name}",
        name=name,
        brand=brand,
        category=category,
        prices=[ProviderPrice(provider=provider, price=999)],
    )


def test_identity_engine_returns_fingerprint_and_exact_tier() -> None:
    result = identity_engine.compare(
        user_query="Sony WH-CH520 Wireless Headphones",
        selected_product={"name": "Sony WH-CH520 Wireless Headphones", "brand": "Sony"},
        category="Shopping",
        provider_product=_product("Sony WH-CH520 Wireless Bluetooth Headphones", "Sony"),
    )
    assert result.match_tier in {"exact", "probable"}
    assert result.match_score >= 0.55
    assert len(result.identity_fingerprint) == 24
    assert result.identity_factors["candidate"]["brand"] == "sony"


def test_identity_engine_rejects_dangerous_lookalike() -> None:
    result = identity_engine.compare(
        user_query="Noise Airwave Max 6 Bluetooth",
        selected_product={"name": "Noise Airwave Max 6 Bluetooth", "brand": "Noise"},
        category="Shopping",
        provider_product=_product("Noise Airwave Max 2 50H Battery Bluetooth Headphones", "Noise", "Flipkart"),
    )
    assert result.match_tier == "rejected"
    assert result.match_score < 0.55
    assert "number" in (result.rejection_reason or "").lower()


def test_identity_engine_rejects_wrong_travel_route() -> None:
    result = identity_engine.compare(
        user_query="Delhi to Mumbai flight",
        selected_product={"name": "Delhi to Mumbai flight"},
        category="Travel",
        provider_product=_product("Delhi to Bengaluru flight", "MakeMyTrip", "MakeMyTrip", "Travel"),
    )
    assert result.match_tier == "rejected"
    assert result.rejection_reason == "Route does not match"
