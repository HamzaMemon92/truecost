import pytest
from app.providers.mock_grocery_provider import MockFastGroceryProvider, MockCheapGroceryProvider
from app.schemas.grocery import SearchIntent, Location

@pytest.fixture
def provider():
    return MockFastGroceryProvider()

@pytest.fixture
def provider_zepto():
    return MockCheapGroceryProvider()

@pytest.mark.asyncio
async def test_deep_link_exact_sku_mapping(provider):
    query = "Amul Taaza Milk"
    location = Location(postal_code="110001")
    results = await provider.search(query, location)
    
    amul_1l = next((r for r in results if r["canonical_product_id"] == "amul-taaza-toned-milk-1l"), None)
    amul_500ml = next((r for r in results if r["canonical_product_id"] == "amul-taaza-toned-milk-500ml"), None)
    
    assert amul_1l is not None
    assert amul_500ml is not None
    
    assert amul_1l["deep_link_url"] is not None
    assert amul_500ml["deep_link_url"] is not None
    
    # Prove they don't map to the same URL
    assert amul_1l["deep_link_url"] != amul_500ml["deep_link_url"]
    assert "amul-taaza-toned-milk-1l" in amul_1l["deep_link_url"]
    assert "amul-taaza-toned-milk-500ml" in amul_500ml["deep_link_url"]

@pytest.mark.asyncio
async def test_retailer_cross_leakage(provider, provider_zepto):
    query = "Amul Taaza Milk 1L"
    location = Location(postal_code="110001")
    
    blinkit_results = await provider.search(query, location)
    zepto_results = await provider_zepto.search(query, location)
    
    blinkit_1l = next((r for r in blinkit_results if r["canonical_product_id"] == "amul-taaza-toned-milk-1l"), None)
    zepto_1l = next((r for r in zepto_results if r["canonical_product_id"] == "amul-taaza-toned-milk-1l"), None)
    
    assert blinkit_1l["deep_link_url"] is not None
    assert zepto_1l["deep_link_url"] is not None
    
    # Prove Retailer A does not leak into Retailer B
    assert blinkit_1l["deep_link_url"] != zepto_1l["deep_link_url"]
    assert "mockfastgrocery" in blinkit_1l["deep_link_url"]
    assert "mockcheapgrocery" in zepto_1l["deep_link_url"]

@pytest.mark.asyncio
async def test_unavailable_offer_has_no_deep_link(provider):
    query = "Amul Milk"
    location = Location(postal_code="000000") # Out of service area usually sets UNAVAILABLE_IN_AREA
    
    # We force availability out of area to test fallback
    results = await provider.search(query, location)
    for r in results:
        if r["availability"] == "UNAVAILABLE_IN_AREA":
            assert r["deep_link_type"] == "UNAVAILABLE"
            assert r["deep_link_url"] is None
