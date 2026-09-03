import pytest
import asyncio
from typing import Any

from app.providers.mock_ondc_provider import MockOndcProvider
from app.providers.grocery_base import normalize_grocery_results
from app.graph.grocery_workflow import compile_grocery_workflow
from app.graph.grocery_state import GroceryGraphState

@pytest.mark.asyncio
async def test_ondc_mock_provider_raw():
    provider = MockOndcProvider()
    results = await provider.search("amul milk")
    
    assert len(results) == 4
    # All 4 items should be distinct Retailer Offers
    provider_skus = [item["provider_sku"] for item in results]
    assert len(set(provider_skus)) == 4
    
    # 3 items should share the 1L GTIN
    gtin_1l = "amul-taaza-toned-milk-1l"
    items_1l = [item for item in results if item["canonical_product_id"] == gtin_1l]
    assert len(items_1l) == 3
    
    # 1 item should have the 500ml GTIN
    gtin_500 = "amul-taaza-toned-milk-500ml"
    items_500 = [item for item in results if item["canonical_product_id"] == gtin_500]
    assert len(items_500) == 1

    # Verify source type and image confidence are securely bounded
    for item in results:
        assert item["source_type"] == "mock", "Mock provider must never emit 'live' source_type"
        assert item["image_confidence"] == "KNOWN_SOURCE", "ONDC images must not be blindly TRUSTED"

@pytest.mark.asyncio
async def test_ondc_deduplication_via_orchestrator(monkeypatch):
    """
    Test that the orchestrator groups the 3 distinct ONDC sellers into
    a SINGLE canonical product with 3 RetailerOffers, and the 500ml variant
    into a SEPARATE canonical product.
    """
    # Pre-fetch mock results
    from app.providers.mock_ondc_provider import MockOndcProvider
    from app.providers.grocery_base import normalize_grocery_results
    ondc = MockOndcProvider()
    res = await ondc.search("amul milk")
    normalized = normalize_grocery_results(ondc, res)
    mock_results = [r.model_dump() if hasattr(r, "model_dump") else r for r in normalized]

    def fake_search_observations(self, query: str, providers: list[str] | None = None):
        return mock_results

    monkeypatch.setattr(
        "app.repositories.grocery_observation_repository.GroceryObservationRepository.search_observations_as_canonical",
        fake_search_observations
    )

    state = {
        "items": ["amul milk"],
        "category": "grocery",
        "session_id": "test-session",
        "user_id": "test-user",
        "preferences": {},
        "force_deep_agent": False,
        "context": {},
        "complexity": "simple",
        "route": "direct-basket",
        "agent_type": None,
        "mcp_tools_used": [],
        "mcp_results": [],
        "evidence": [],
        "basket_results": [],
        "recommended_basket": None,
        "alternative_baskets": [],
        "substitutions": [],
        "verification": [],
        "reasoning": [],
        "response": {},
    }
    
    workflow = compile_grocery_workflow()
    result_state = await workflow.ainvoke(state)
    
    # The grocery workflow returns grouped comparisons in 'product_comparisons'
    product_comparisons = result_state.get("product_comparisons", [])
    assert product_comparisons is not None
    
    # We should have exactly 2 canonical items: 1L and 500ml
    assert len(product_comparisons) >= 2
    
    # Find the 1L item
    item_1l = next(item for item in product_comparisons if item["product"]["canonical_product_id"] == "amul-taaza-toned-milk-1l")
    # It must have 3 distinct seller offers from ONDC (and potentially other mock providers)
    assert len(item_1l["offers"]) >= 3
    
    seller_names = [offer["provider"] for offer in item_1l["offers"]]
    assert "ONDC Seller seller_A" in seller_names
    assert "ONDC Seller seller_B" in seller_names
    assert "ONDC Seller seller_C" in seller_names
    
    # Check pricing bounds logic applies across ONDC sellers
    offer_a = next(o for o in item_1l["offers"] if o["provider"] == "ONDC Seller seller_A")
    assert offer_a["price"] == 68.0
    
    offer_c = next(o for o in item_1l["offers"] if o["provider"] == "ONDC Seller seller_C")
    assert offer_c["price"] == 65.0
    assert offer_c["availability"] == "OUT_OF_STOCK"
    
    # Ensure OUT_OF_STOCK seller doesn't win cheapest
    assert item_1l["winners"]["cheapest"] != "ONDC Seller seller_C"
    
    # Find the 500ml item
    item_500 = next(item for item in product_comparisons if item["product"]["canonical_product_id"] == "amul-taaza-toned-milk-500ml")
    seller_names_500 = [offer["provider"] for offer in item_500["offers"]]
    assert "ONDC Seller seller_A" in seller_names_500
    assert item_500["product"]["normalized_quantity"] == 0.5
