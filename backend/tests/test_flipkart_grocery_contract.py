import pytest
import datetime
from app.providers.flipkart_grocery_provider import FlipkartGroceryProvider, _parse_quantity, RateLimitError
from app.schemas.grocery import CanonicalGroceryItem

def test_parse_quantity():
    # Test valid parsing
    assert _parse_quantity("Amul Taaza Toned Milk 500 ml", "") == (500.0, "ml")
    assert _parse_quantity("Aashirvaad Whole Wheat Atta", "1 kg") == (1.0, "kg")
    assert _parse_quantity("Lays Classic 50g", "") == (50.0, "g")
    
    # Test missing parsing
    assert _parse_quantity("Generic Item", "") == (1.0, "unit")


@pytest.mark.asyncio
async def test_flipkart_grocery_mapping(monkeypatch):
    provider = FlipkartGroceryProvider()
    
    # Mock settings so it appears "live" for testing the mapping logic properly
    monkeypatch.setattr("app.providers.flipkart_grocery_provider.settings.flipkart_affiliate_id", "test_id")
    monkeypatch.setattr("app.providers.flipkart_grocery_provider.settings.flipkart_affiliate_token", "test_token")
    
    # Fake response data from Flipkart Affiliate API
    mock_response = {
        "productInfoList": [
            {
                # Valid Product
                "productBaseInfoV1": {
                    "title": "Aashirvaad Whole Wheat Atta",
                    "productBrand": "Aashirvaad",
                    "productId": "GROC12345",
                    "categoryPath": "Grocery>Staples>Atta",
                    "sellingPrice": {"amount": 250.0},
                    "maximumRetailPrice": {"amount": 280.0},
                    "inStock": "true",
                    "productUrl": "https://flipkart.com/aashirvaad-atta/p/groc12345",
                    "imageUrls": {"400x400": "https://img.fk.com/400x400.jpg"},
                    "attributes": "5 kg"
                }
            },
            {
                # Missing title, should be rejected
                "productBaseInfoV1": {
                    "productId": "BAD123"
                }
            },
            {
                # Invalid negative price
                "productBaseInfoV1": {
                    "title": "Invalid Price Item",
                    "sellingPrice": {"amount": -50.0},
                    "productId": "BAD456"
                }
            },
            {
                # Missing image
                "productBaseInfoV1": {
                    "title": "No Image Product",
                    "sellingPrice": {"amount": 100.0},
                    "productId": "NOIMG123",
                    "inStock": "false",
                    "productUrl": "https://flipkart.com/no-img/p/noimg123",
                }
            },
            {
                # Malformed version structure (no productBaseInfoV1)
                "productBaseInfoV2": {
                    "title": "Future Version",
                    "sellingPrice": 100.0
                }
            }
        ]
    }
    
    class MockResponse:
        def raise_for_status(self): pass
        def json(self): return mock_response
    
    class MockClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        async def get(self, *args, **kwargs): return MockResponse()
        
    monkeypatch.setattr("app.providers.flipkart_grocery_provider.httpx.AsyncClient", MockClient)
    
    results = await provider.search("Aashirvaad Atta")
    
    # 2 items should map successfully (Valid product, No Image product)
    assert len(results) == 2
    
    # Verify Valid Product Mapping
    item1 = results[0]
    assert item1.title == "Aashirvaad Whole Wheat Atta"
    assert item1.price == 250.0
    assert item1.delivery_fee is None  # Ensures we don't fabricate zero
    assert item1.min_order_value is None # Ensures we don't fabricate zero
    assert item1.source_type == "live"
    assert item1.availability == "In Stock"
    assert item1.image_verified is False # Image proves source, not SKU identity
    assert item1.image_source == "Flipkart Grocery"
    assert item1.freshness == "UNKNOWN" # Let freshness policy handle this
    assert item1.delivery_minutes is None # Do not fabricate quick-commerce ETA
    
    # Verify Missing Image Product
    item2 = results[1]
    assert item2.title == "No Image Product"
    assert item2.availability == "Out of Stock"
    assert item2.retailer_image_url is None
    assert item2.image_source is None
    

@pytest.mark.asyncio
async def test_flipkart_rate_limit(monkeypatch):
    provider = FlipkartGroceryProvider()
    monkeypatch.setattr("app.providers.flipkart_grocery_provider.settings.flipkart_affiliate_id", "test_id")
    monkeypatch.setattr("app.providers.flipkart_grocery_provider.settings.flipkart_affiliate_token", "test_token")
    
    class MockRateLimitResponse:
        status_code = 429
        headers = {"Retry-After": "10"}
        
    class MockHTTPStatusError(Exception):
        def __init__(self):
            self.response = MockRateLimitResponse()
            
    class MockClientRateLimit:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        async def get(self, *args, **kwargs): 
            raise MockHTTPStatusError()
            
    monkeypatch.setattr("app.providers.flipkart_grocery_provider.httpx.AsyncClient", MockClientRateLimit)
    import httpx
    monkeypatch.setattr("app.providers.flipkart_grocery_provider.httpx.HTTPStatusError", MockHTTPStatusError)
    
    with pytest.raises(RateLimitError) as exc_info:
        await provider.search("Atta")
        
    assert "Retry-After: 10" in str(exc_info.value)

    
