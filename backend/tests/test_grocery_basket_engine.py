import pytest
from app.schemas.grocery import CanonicalGroceryItem, CanonicalBasket
from app.graph.grocery_basket_engine import BasketBuilder, CostCalculator, ConstraintEngine, BasketOptimizer

def make_item(provider: str, title: str, price: float) -> CanonicalGroceryItem:
    return CanonicalGroceryItem(
        canonical_product_id="test",
        provider=provider,
        provider_sku="sku",
        title=title,
        brand="brand",
        category="cat",
        quantity_value=1.0,
        quantity_unit="unit",
        price=price,
        availability="In Stock",
        source_url="url",
        affiliate_url="url",
        source_type="mock",
    )

def test_basket_builder():
    items = [
        make_item("ProviderA", "Milk", 50),
        make_item("ProviderA", "Bread", 40),
        make_item("ProviderB", "Milk", 48),
    ]
    baskets = BasketBuilder.build(items)
    
    assert len(baskets) == 2
    b_a = next(b for b in baskets if b.provider == "ProviderA")
    assert len(b_a.items) == 2
    
    b_b = next(b for b in baskets if b.provider == "ProviderB")
    assert len(b_b.items) == 1


def test_cost_calculator():
    # Test MockFastGrocery (high fees, 10 min)
    b_fast = CanonicalBasket(
        provider="MockFastGrocery",
        items=[make_item("MockFastGrocery", "Milk", 100)],
        subtotal=0, delivery_fee=0, platform_fee=0, final_total=0,
        meets_minimum_order=True, estimated_delivery=None
    )
    b_fast = CostCalculator.calculate(b_fast)
    
    assert b_fast.subtotal == 100.0
    assert b_fast.delivery_fee == 69.0  # 49 (subtotal < 200) + 20 (fast)
    assert b_fast.platform_fee == 5.0
    assert b_fast.final_total == 174.0
    assert b_fast.meets_minimum_order is True  # fast min order is 100
    assert b_fast.estimated_delivery == "10 minutes"
    
    # Test MockCheapGrocery (low fees, 30 min)
    b_cheap = CanonicalBasket(
        provider="MockCheapGrocery",
        items=[make_item("MockCheapGrocery", "Milk", 100)],
        subtotal=0, delivery_fee=0, platform_fee=0, final_total=0,
        meets_minimum_order=True, estimated_delivery=None
    )
    b_cheap = CostCalculator.calculate(b_cheap)
    assert b_cheap.delivery_fee == 15.0  # Cheap mock rule for < 200
    assert b_cheap.estimated_delivery == "30 minutes"
    assert b_cheap.meets_minimum_order is True # cheap min order is 50


def test_constraint_engine():
    b = CanonicalBasket(
        provider="Test",
        items=[make_item("Test", "Golden Organic Milk", 100)],
        subtotal=0, delivery_fee=0, platform_fee=0, final_total=0,
        meets_minimum_order=True, estimated_delivery=None
    )
    # Query for milk should be found. Query for eggs should be missing.
    b = ConstraintEngine.evaluate(b, ["1 milk", "1 dozen eggs"])
    assert "1 dozen eggs" in b.missing_items
    assert "1 milk" not in b.missing_items


def test_basket_optimizer():
    # Construct mock baskets with calculated costs and constraints
    b_fast = CanonicalBasket(
        provider="Fast",
        items=[], subtotal=300, delivery_fee=50, platform_fee=5, final_total=355,
        meets_minimum_order=True, estimated_delivery="10 minutes", missing_items=[]
    )
    
    b_cheap = CanonicalBasket(
        provider="Cheap",
        items=[], subtotal=200, delivery_fee=15, platform_fee=5, final_total=220,
        meets_minimum_order=True, estimated_delivery="30 minutes", missing_items=[]
    )
    
    b_incomplete = CanonicalBasket(
        provider="Incomplete",
        items=[], subtotal=100, delivery_fee=10, platform_fee=5, final_total=115,
        meets_minimum_order=True, estimated_delivery="15 minutes", missing_items=["eggs"]
    )
    
    baskets = [b_fast, b_cheap, b_incomplete]
    
    # Cheapest objective should pick b_cheap (b_incomplete is cheaper but has huge missing penalty)
    ranked_cheap = BasketOptimizer.optimize(baskets, "cheapest")
    assert ranked_cheap[0].provider == "Cheap"
    
    # Fastest objective should pick b_fast
    ranked_fast = BasketOptimizer.optimize(baskets, "fastest")
    assert ranked_fast[0].provider == "Fast"
