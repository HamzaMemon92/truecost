import pytest
from app.services.grocery.basket import BasketOptimizerService
from app.schemas.grocery import CanonicalGroceryItem

def test_negative_effective_price_prevention():
    # If a discount is somehow greater than the price, it should cap at 0
    item = CanonicalGroceryItem(
        canonical_product_id="test-item",
        title="Test Item",
        brand="Test",
        category="Test",
        quantity_value=1.0,
        quantity_unit="pc",
        price=10.0,
        discount=15.0, # Intentional large discount
        availability="IN_STOCK",
        provider="mock",
        provider_sku="mock",
        deep_link_type="UNAVAILABLE",
        source_url="http://mock.com",
        affiliate_url="http://mock.com",
        source_type="mock"
    )
    
    catalog = {"test-item": item}
    basket_items = {"test-item": 2}
    assigned_ids = {"test-item"}
    
    service = BasketOptimizerService()
    fg = service._build_fulfillment_group("mock", catalog, basket_items, assigned_ids)
    
    # Unit price = max(0, 10 - 15) = 0.
    # subtotal = 0 * 2 = 0
    assert fg.subtotal == 0.0
    
    # Subtotal < 200, so delivery fee = 49.0
    # Platform fee = 5.0
    # Final total = 54.0
    assert fg.final_total == 54.0

def test_basket_rounding():
    item = CanonicalGroceryItem(
        canonical_product_id="test-item",
        title="Test Item",
        brand="Test",
        category="Test",
        quantity_value=1.0,
        quantity_unit="pc",
        price=10.555, # Weird float
        discount=0.0,
        availability="IN_STOCK",
        provider="mock",
        provider_sku="mock",
        deep_link_type="UNAVAILABLE",
        source_url="http://mock.com",
        affiliate_url="http://mock.com",
        source_type="mock"
    )
    
    catalog = {"test-item": item}
    basket_items = {"test-item": 3}
    assigned_ids = {"test-item"}
    
    service = BasketOptimizerService()
    fg = service._build_fulfillment_group("mock", catalog, basket_items, assigned_ids)
    
    # 10.555 * 3 = 31.665. Should be rounded to 31.66 due to bankers rounding
    assert fg.subtotal == 31.66
    assert fg.final_total == 31.66 + 49.0 + 5.0
