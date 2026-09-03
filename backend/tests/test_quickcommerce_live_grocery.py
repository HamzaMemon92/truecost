import pytest
import os
import asyncio
from app.providers.quickcommerce_provider import QuickCommerceProvider
from app.config import settings
from app.schemas.grocery import Location

@pytest.mark.asyncio
async def test_quickcommerce_live_grocery():
    """
    Live end-to-end integration test for QuickCommerce provider.
    
    As per Phase 2.6 requirements, this test MUST SKIP cleanly if live
    credentials are not configured in the environment. It must NOT fake
    live execution using mock data.
    """
    print("\nQuickCommerce API configuration:")
    
    is_configured = bool(settings.quickcommerce_api_key)
    print(f"configured: {str(is_configured).lower()}")
    print(f"api_key_present: {str(is_configured).lower()}")
    
    if not is_configured:
        pytest.skip("LIVE QUICKCOMMERCE TEST BLOCKED — API KEY NOT CONFIGURED")
        
    provider = QuickCommerceProvider()
    
    assert provider.status == "active"
    assert provider.source_type == "live"
    
    # We will search with a hardcoded valid location (Bangalore) to guarantee serviceability
    location = Location(latitude=12.9716, longitude=77.5946)
    
    results = await provider.search("Amul Butter 500g", location=location)
    
    # There should be results from at least one platform if it's working
    assert len(results) > 0, "Live API returned empty results for a very common query"
    
    # Validate canonical mapping
    item = results[0]
    
    assert item.provider in ["Blinkit", "Zepto", "SwiggyInstamart", "Swiggy"]
    assert item.source_type == "live"
    assert item.price > 0
    assert item.availability in ["In Stock", "Out of Stock"]
    assert getattr(item, "delivery_minutes", None) is not None, "At least one provider should return ETA"
    assert item.retrieved_at is not None
    assert item.image_verified is False
    assert item.image_source == "provider"
    
    # Let's ensure the request didn't accidentally fallback to a mock provider
    assert item.provider != "Mock"
