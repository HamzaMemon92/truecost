import pytest
import os
import asyncio
from app.providers.flipkart_grocery_provider import FlipkartGroceryProvider
from app.config import settings

@pytest.mark.asyncio
async def test_flipkart_grocery_live_search():
    """
    Live end-to-end integration test for Flipkart Grocery.
    
    As per Phase 2.5 requirements, this test MUST SKIP cleanly if live
    credentials are not configured in the environment. It must NOT fake
    live execution using mock data.
    """
    print("\nFlipkart Affiliate configuration:")
    
    is_configured = bool(settings.flipkart_affiliate_id and settings.flipkart_affiliate_token)
    print(f"configured: {str(is_configured).lower()}")
    print(f"affiliate_id_present: {str(bool(settings.flipkart_affiliate_id)).lower()}")
    print(f"affiliate_token_present: {str(bool(settings.flipkart_affiliate_token)).lower()}")
    
    if not is_configured:
        pytest.skip("SKIPPED — FLIPKART LIVE CREDENTIALS NOT CONFIGURED")
        
    provider = FlipkartGroceryProvider()
    
    # Verify the status dynamically reflects live access
    assert provider.status == "active"
    assert provider.source_type == "live"
    
    # Call the actual live endpoint
    results = await provider.search("Amul Milk")
    
    # We should get results if the API is working
    assert len(results) > 0, "Live API returned empty results for a very common query"
    
    item = results[0]
    
    # Assert Canonical schema mapping from live data
    assert item.provider == "Flipkart Grocery"
    assert item.source_type == "live"
    assert item.price > 0
    assert item.availability in ["In Stock", "Out of Stock"]
    assert "flipkart.com" in item.source_url
    assert item.deep_link_type == "PRODUCT_PAGE"
    assert item.deep_link_url is not None
    assert "flipkart.com" in item.deep_link_url
    assert item.freshness == "UNKNOWN"
    assert item.price_checked_at is not None
