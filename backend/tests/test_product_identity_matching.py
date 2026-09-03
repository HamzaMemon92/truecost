from app.category_catalog import CATALOG, provider_ids_for_engine_category
from app.schemas.product import ProviderPrice, TrueCostProduct
from app.services.merger import merge_products
from app.services.relevance import score_exact_product, score_product


def product(name: str, brand: str, provider: str, price: float, category: str = "Shopping") -> TrueCostProduct:
    return TrueCostProduct(
        id=f"{provider.lower()}-{abs(hash((name, brand))) % 100000}",
        name=name,
        brand=brand,
        category=category,
        prices=[ProviderPrice(provider=provider, price=price)],
    )


def test_exact_product_matching_across_realistic_catalog_cases() -> None:
    cases = [
        ("Noise Airwave Max 6 Bluetooth", "Noise Airwave Max 6, 50H Battery, 40mm Driver Bluetooth", "Noise", True),
        ("Noise Airwave Max 6 Bluetooth", "Noise Airwave Max 2, 50H Battery Bluetooth Headphones", "Noise", False),
        ("Noise Airwave Max 6 Bluetooth", "TechFusion BT MAX Neckband", "TechFusion", False),
        ("iPhone 15 128GB Blue", "Apple iPhone 15 (128 GB) - Blue", "Apple", True),
        ("iPhone 15 128GB Blue", "Apple iPhone 14 128GB Blue", "Apple", False),
        ("Samsung Galaxy S24 Ultra", "Samsung Galaxy S24 Ultra 5G", "Samsung", True),
        ("Samsung Galaxy S24 Ultra", "Samsung Galaxy S23 Ultra 5G", "Samsung", False),
        ("Amul Taaza Milk 1L", "Amul Taaza Toned Milk 1 L", "Amul", True),
        ("Amul Taaza Milk 1L", "Amul Gold Full Cream Milk 1 L", "Amul", False),
        ("Dolo 650 tablet", "Dolo 650 Tablet Strip", "Micro Labs", True),
        ("Dolo 650 tablet", "Paracetamol 500 Tablet", "Generic", False),
        ("Dominos Margherita Pizza", "Domino's Margherita Pizza Regular", "Dominos", True),
        ("Dominos Margherita Pizza", "Pizza Hut Margherita Pizza", "Pizza Hut", False),
        ("Uber Premier", "Uber Premier ride", "Uber", True),
        ("Uber Premier", "Uber Go ride", "Uber", False),
        ("Delhi to Mumbai flight", "Delhi to Mumbai non-stop flight", "MakeMyTrip", True),
        ("Delhi to Mumbai flight", "Delhi to Bengaluru flight", "MakeMyTrip", False),
        ("Taj Palace Delhi", "Taj Palace New Delhi", "Taj", True),
        ("Taj Palace Delhi", "The Park New Delhi", "The Park", False),
        ("HDFC Millennia Credit Card", "HDFC Millennia Credit Card", "HDFC", True),
        ("HDFC Millennia Credit Card", "ICICI Amazon Pay Credit Card", "ICICI", False),
        ("Notion Plus plan", "Notion Plus monthly plan", "Notion", True),
        ("Notion Plus plan", "Slack Pro plan", "Slack", False),
    ]

    false_positives: list[tuple[str, str, float]] = []
    false_negatives: list[tuple[str, str, float]] = []
    for query, candidate, brand, should_match in cases:
        score = score_exact_product(query, candidate, brand)
        matched = score >= 0.55
        if matched and not should_match:
            false_positives.append((query, candidate, score))
        if should_match and not matched:
            false_negatives.append((query, candidate, score))

    assert false_positives == []
    assert false_negatives == []


def test_discovery_can_surface_related_items_without_promoting_them_to_exact_prices() -> None:
    assert score_product("noise headphones", "Bluetooth Headphones & Earphones", "Meesho") >= 0.35
    assert score_exact_product("Noise Airwave Max 6 Bluetooth", "Bluetooth Headphones & Earphones", "Meesho") < 0.55


def test_merger_preserves_model_variants_but_merges_same_product_offers() -> None:
    merged = merge_products([
        product("Noise Airwave Max 6 Bluetooth", "Noise", "Amazon", 1899),
        product("Noise Airwave Max 6, 50H Battery Bluetooth", "Noise", "Flipkart", 1799),
        product("Noise Airwave Max 2 50H Battery Bluetooth", "Noise", "Meesho", 1299),
        product("Amul Taaza Milk 1L", "Amul", "Zepto", 72, "Grocery"),
        product("Amul Taaza Toned Milk 1 L", "Amul", "Blinkit", 74, "Grocery"),
    ], threshold=0.72)

    names = [item.name for item in merged]
    max6 = next(item for item in merged if item.name.startswith("Noise Airwave Max 6"))
    assert len(max6.prices) == 2
    assert any(item.name.startswith("Noise Airwave Max 2") for item in merged)
    assert len([name for name in names if name.startswith("Amul Taaza")]) == 1


def test_every_category_has_scoped_provider_comparison_surface() -> None:
    counts = {category.name: len(provider_ids_for_engine_category(category.engine_category)) for category in CATALOG.categories}
    assert counts == {
        "Grocery": 4,
        "Food": 4,
        "Pharmacy": 4,
        "Shopping": 4,
        "Mobility": 4,
        "Flights": 4,
        "Hotels": 0,
        "Deals": 0,
        "Finance": 4,
        "Services": 4,
    }
    assert sum(counts.values()) == 32
