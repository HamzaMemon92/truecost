import pytest
from app.schemas.grocery import (
    CanonicalGroceryItem,
    TrueCostBasketItem,
    BasketEvaluationRequest
)
from app.services.grocery.basket import BasketOptimizerService

def make_item(provider: str, c_id: str, price: float, availability: str = "IN_STOCK") -> CanonicalGroceryItem:
    return CanonicalGroceryItem(
        canonical_product_id=c_id,
        provider=provider,
        provider_sku=c_id + "-sku",
        title=c_id,
        brand="brand",
        category="cat",
        quantity_value=1.0,
        quantity_unit="unit",
        price=price,
        availability=availability,
        source_url="url",
        affiliate_url="url",
        source_type="mock",
    )

def test_single_retailer_completeness():
    """
    Test:
    Retailer A: 3/3 items ₹150
    Retailer B: 2/3 items ₹100
    Retailer B MUST NOT win the 'complete basket' comparison.
    """
    available_items = [
        make_item("RetailerA", "item1", 50),
        make_item("RetailerA", "item2", 50),
        make_item("RetailerA", "item3", 50),
        make_item("RetailerB", "item1", 50),
        make_item("RetailerB", "item2", 50),
        # Retailer B is missing item3
    ]
    
    req = BasketEvaluationRequest(
        items=[
            TrueCostBasketItem(canonical_product_id="item1", quantity=1),
            TrueCostBasketItem(canonical_product_id="item2", quantity=1),
            TrueCostBasketItem(canonical_product_id="item3", quantity=1),
        ],
        mode="CHEAPEST"
    )
    
    results = BasketOptimizerService.evaluate(req, available_items)
    
    # Best result should be Retailer A (or split A+B, but we want to ensure B doesn't win alone)
    # Retailer A has total = 150 + 49 delivery + 5 platform = 204
    # Split A+B has total = (A: 50 + 49 + 5) + (B: 100 + 49 + 5) = 258
    # Therefore, A alone should win
    assert results[0].retailer_count == 1
    assert results[0].fulfillment_groups[0].provider == "RetailerA"
    assert len(results[0].unavailable_items) == 0

def test_split_basket_optimization():
    """
    Test:
    Retailer A: all items ₹170
    Retailer B + C: all items ₹150 2 deliveries
    The system should correctly identify B+C as the cheaper split basket while clearly exposing the two-delivery tradeoff.
    """
    available_items = [
        # Retailer A has all 3, but is expensive
        make_item("RetailerA", "item1", 60),
        make_item("RetailerA", "item2", 60),
        make_item("RetailerA", "item3", 50),
        
        # Retailer B has 1 and 2, but cheap
        make_item("RetailerB", "item1", 25),
        make_item("RetailerB", "item2", 25),
        
        # Retailer C has 3, but cheap
        make_item("RetailerC", "item3", 20),
    ]
    
    req = BasketEvaluationRequest(
        items=[
            TrueCostBasketItem(canonical_product_id="item1", quantity=1),
            TrueCostBasketItem(canonical_product_id="item2", quantity=1),
            TrueCostBasketItem(canonical_product_id="item3", quantity=1),
        ],
        mode="CHEAPEST"
    )
    
    results = BasketOptimizerService.evaluate(req, available_items)
    
    # Retailer A total: 170 + 49 + 5 = 224
    # B + C total: B(50 + 49 + 5 = 104) + C(20 + 49 + 5 = 74) = 178
    # So B + C should win
    best = results[0]
    
    # We bounded split optimization to only pairs (if there are >= 2 providers)
    assert best.retailer_count == 2
    providers = {fg.provider for fg in best.fulfillment_groups}
    assert providers == {"RetailerB", "RetailerC"}
    assert best.deliveries == 2
    
    # Check that savings are correctly exposed
    # Savings vs worst standard (RetailerA = 224). 224 - 178 = 46.
    assert best.savings == 46.0
    
    # Now check SINGLE_RETAILER mode
    req_single = BasketEvaluationRequest(
        items=[
            TrueCostBasketItem(canonical_product_id="item1", quantity=1),
            TrueCostBasketItem(canonical_product_id="item2", quantity=1),
            TrueCostBasketItem(canonical_product_id="item3", quantity=1),
        ],
        mode="SINGLE_RETAILER"
    )
    results_single = BasketOptimizerService.evaluate(req_single, available_items)
    best_single = results_single[0]
    assert best_single.retailer_count == 1
    assert best_single.fulfillment_groups[0].provider == "RetailerA"
