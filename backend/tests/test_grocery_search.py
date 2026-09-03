from __future__ import annotations

import pytest

from app.services.grocery.intent_parser import parse_grocery_intent
from app.services.grocery.matching import match_products
from app.providers.canonical_catalog import get_canonical_catalog
from app.providers.mock_grocery_provider import MockGoldenGroceryProvider, MockFastGroceryProvider, MockCheapGroceryProvider

def test_intent_parsing_milk():
    intent = parse_grocery_intent("milk")
    assert intent.category == "dairy"
    assert intent.variant == "milk"

def test_intent_parsing_amul_milk():
    intent = parse_grocery_intent("amul milk")
    assert intent.brand == "amul"
    assert intent.category == "dairy"

def test_intent_parsing_amul_taaza_1_litre():
    intent = parse_grocery_intent("amul taaza 1 litre")
    assert intent.brand == "amul"
    assert intent.normalized_quantity == 1.0
    assert intent.normalized_unit == "L"
    assert "taaza" in intent.remaining_terms

def test_intent_parsing_full_cream_milk():
    intent = parse_grocery_intent("full cream milk")
    assert intent.category == "dairy"
    assert "full cream" in intent.remaining_terms

def test_intent_parsing_milk_under_60():
    intent = parse_grocery_intent("milk under 60")
    assert intent.category == "dairy"
    assert intent.max_price == 60.0

def test_intent_parsing_milk_500_ml():
    intent = parse_grocery_intent("milk 500 ml")
    assert intent.normalized_quantity == 0.5
    assert intent.normalized_unit == "L"

def test_intent_parsing_2_litre_milk():
    intent = parse_grocery_intent("2 litre milk")
    assert intent.normalized_quantity == 2.0
    assert intent.normalized_unit == "L"

def test_intent_parsing_eggs():
    intent = parse_grocery_intent("6 eggs")
    assert intent.category == "eggs"
    assert intent.pack_count == 6

def test_intent_parsing_bread():
    intent = parse_grocery_intent("britannia bread")
    assert intent.brand == "britannia"
    assert intent.category == "bakery"

def test_matching_brand_quantity_variant():
    catalog = get_canonical_catalog()
    intent = parse_grocery_intent("amul taaza milk 500ml")
    matches = match_products(intent, catalog)
    
    assert len(matches) > 0
    top_match = matches[0][0]
    
    assert top_match.brand == "Amul"
    assert top_match.normalized_quantity == 0.5
    assert top_match.normalized_unit == "L"
    assert "taaza" in top_match.tags

def test_negative_matching_decoys():
    catalog = get_canonical_catalog()
    intent = parse_grocery_intent("milk")
    matches = match_products(intent, catalog)
    
    # Decoys are "steel-milk-pan-1l" (cookware) and "pedigree-dog-food-milk-1kg" (pets)
    # The matching engine filters strictly by category if it's detected.
    # Since "milk" resolves to category="dairy", decoys should be completely excluded.
    
    decoy_ids = ["steel-milk-pan-1l", "pedigree-dog-food-milk-1kg"]
    for match, score, _ in matches:
        assert match.canonical_product_id not in decoy_ids

def test_price_constraint():
    catalog = get_canonical_catalog()
    # We have 1L milk for 54 and 500ml for 27.
    intent = parse_grocery_intent("amul milk under 50")
    matches = match_products(intent, catalog)
    
    for match, score, _ in matches:
        assert match.base_price_estimate <= 50.0

@pytest.mark.asyncio
async def test_mock_providers_pricing_multiplier():
    golden = MockGoldenGroceryProvider()
    fast = MockFastGroceryProvider()
    cheap = MockCheapGroceryProvider()
    
    q = "amul taaza 1L"
    
    g_res = await golden.search(q)
    f_res = await fast.search(q)
    c_res = await cheap.search(q)
    
    # Grab the price of the first result
    g_price = g_res[0]["price"]
    f_price = f_res[0]["price"]
    c_price = c_res[0]["price"]
    
    # fast should be ~1.3x golden
    # cheap should be ~0.8x golden
    assert round(f_price, 2) == round(g_price * 1.3, 2)
    assert round(c_price, 2) == round(g_price * 0.8, 2)
    
    assert f_res[0]["delivery_minutes"] == 10
    assert c_res[0]["delivery_minutes"] == 30

from app.schemas.grocery import Location, RetailerOffer
from app.services.grocery.pricing import calculate_effective_price, calculate_unit_price, rank_offers
from app.services.grocery.comparison import ProductComparison

@pytest.mark.asyncio
async def test_mock_providers_location_availability():
    golden = MockGoldenGroceryProvider()
    fast = MockFastGroceryProvider()
    cheap = MockCheapGroceryProvider()
    
    q = "amul taaza 1L"
    loc_unavailable = Location(postal_code="UNAVAILABLE")
    loc_slow_only = Location(postal_code="SLOW_ONLY")
    loc_cheap_out = Location(postal_code="CHEAP_OUT_OF_STOCK")
    
    # 1. Unavailable entirely
    g_res = await golden.search(q, location=loc_unavailable)
    assert g_res[0]["availability"] == "UNAVAILABLE_IN_AREA"
    
    # 2. Fast is unavailable in SLOW_ONLY
    f_res = await fast.search(q, location=loc_slow_only)
    assert f_res[0]["availability"] == "UNAVAILABLE_IN_AREA"
    g_res2 = await golden.search(q, location=loc_slow_only)
    assert g_res2[0]["availability"] == "IN_STOCK"
    
    # 3. Cheap is out of stock
    c_res = await cheap.search(q, location=loc_cheap_out)
    assert c_res[0]["availability"] == "OUT_OF_STOCK"


def test_pricing_engine_effective_price():
    offer = RetailerOffer(
        provider="MockFast",
        provider_sku="123",
        price=54.0,
        mrp=60.0,
        delivery_fee=20.0,
        platform_fee=5.0,
        discount=10.0,
        coupon_discount=5.0,
        availability="IN_STOCK",
        delivery_minutes=10,
        source_url="http"
    )
    res = calculate_effective_price(offer)
    # 54 + 20 + 5 - 10 - 5 = 64
    assert res.effective_total == 64.0
    bd = res.get_breakdown()
    assert bd["item_price"] == 54.0
    assert bd["delivery_fee"] == 20.0
    assert bd["discount"] == 10.0


def test_unit_price_calculation():
    assert calculate_unit_price(64.0, 1.0, "L") == "₹64.00/L"
    assert calculate_unit_price(32.0, 0.5, "L") == "₹64.00/L"
    assert calculate_unit_price(140.0, 1.0, "kg") == "₹140.00/kg"


def test_ranking_engine_cheapest_vs_fastest():
    offer_cheap_slow = RetailerOffer(
        provider="Cheap", provider_sku="1", price=50.0, availability="IN_STOCK", delivery_minutes=30, source_url="http"
    )
    offer_exp_fast = RetailerOffer(
        provider="Fast", provider_sku="2", price=70.0, availability="IN_STOCK", delivery_minutes=10, source_url="http"
    )
    offer_unavail = RetailerOffer(
        provider="Unavail", provider_sku="3", price=10.0, availability="OUT_OF_STOCK", delivery_minutes=5, source_url="http"
    )
    
    offers = [offer_cheap_slow, offer_exp_fast, offer_unavail]
    
    # Cheapest ranking
    cheapest = rank_offers(offers, "CHEAPEST")
    # unavail should be last despite price=10
    assert cheapest[0][0].provider == "Cheap"
    assert cheapest[1][0].provider == "Fast"
    assert cheapest[2][0].provider == "Unavail"
    
    # Fastest ranking
    fastest = rank_offers(offers, "FASTEST")
    assert fastest[0][0].provider == "Fast"
    assert fastest[1][0].provider == "Cheap"
    assert fastest[2][0].provider == "Unavail"
    
    # Best Value (50 + 30*1 = 80 vs 70 + 10*1 = 80)
    # If they tie, it depends on stable sort, but both are valid.
    best = rank_offers(offers, "BEST_VALUE")
    assert best[-1][0].provider == "Unavail"

