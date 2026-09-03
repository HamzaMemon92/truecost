from __future__ import annotations

from typing import Any

from app.providers.grocery_base import GroceryProvider
from app.schemas.grocery import CanonicalGroceryItem, ProviderStatus, GrocerySourceType
from app.services.grocery.intent_parser import parse_grocery_intent
from app.services.grocery.matching import match_products
from app.providers.canonical_catalog import get_canonical_catalog


class MockGoldenGroceryProvider(GroceryProvider):
    name: str = "MockGoldenGrocery"
    status: ProviderStatus = "active"
    source_type: GrocerySourceType = "mock"
    timeout_ms: int = 4500

    async def search(self, query: str, location: Location | None = None) -> list[CanonicalGroceryItem] | list[dict[str, Any]]:
        # 1. Parse intent
        intent = parse_grocery_intent(query)
        # 2. Get catalog
        catalog = get_canonical_catalog()
        # 3. Match
        matches = match_products(intent, catalog)
        
        results: list[dict[str, Any]] = []
        
        # Take top matches with a score > 0
        valid_matches = [m for m in matches if m[1] > 0]
        
        # Determine availability based on location (mock logic)
        provider_availability = "IN_STOCK"
        if location and location.postal_code == "UNAVAILABLE":
            provider_availability = "UNAVAILABLE_IN_AREA"
        elif location and location.postal_code == "LOW_STOCK":
            provider_availability = "LOW_STOCK"
        
        for product, score, _ in valid_matches[:3]:
            # Sometimes a specific product might be out of stock
            item_availability = provider_availability
            if item_availability == "IN_STOCK" and "eggs" in product.canonical_product_id and location and location.postal_code == "NO_EGGS":
                item_availability = "OUT_OF_STOCK"
                
            results.append({
                "source_url": f"https://mock-{self.name.lower()}.com/product/{product.canonical_product_id}",
                "affiliate_url": f"https://affiliate.com/?url=mock-{self.name.lower()}.com",
                "source_type": "mock",
                "retailer_image_url": product.image_url,
                "image_verified": True,
                "image_source": f"{self.name} Trusted Source",
                "deep_link_type": "PRODUCT_PAGE" if item_availability != "UNAVAILABLE_IN_AREA" else "UNAVAILABLE",
                "deep_link_url": f"https://mock-{self.name.lower()}.com/checkout?sku={product.canonical_product_id}" if item_availability != "UNAVAILABLE_IN_AREA" else None,
                "canonical_product_id": product.canonical_product_id,
                "title": product.title,
                "brand": product.brand,
                "category": product.category,
                "quantity_value": product.normalized_quantity,
                "quantity_unit": product.normalized_unit,
                "price": product.base_price_estimate,
                "mrp": product.base_price_estimate * 1.1, # Fake MRP slightly higher
                "availability": item_availability,
                "delivery_minutes": 15,
                "min_order_value": 0.0,
                "delivery_fee": 20.0,
                "platform_fee": 5.0,
            })
            
        return results


class MockFastGroceryProvider(MockGoldenGroceryProvider):
    name: str = "MockFastGrocery"
    
    async def search(self, query: str, location: Location | None = None) -> list[dict[str, Any]]:
        results = await super().search(query, location)
        
        # Fast provider is unavailable in SLOW_ONLY area
        if location and location.postal_code == "SLOW_ONLY":
            for r in results:
                r["availability"] = "UNAVAILABLE_IN_AREA"
                
        for r in results:
            r["price"] = round(r["price"] * 1.3, 2)  # 30% more expensive
            r["delivery_minutes"] = 10
            r["delivery_fee"] = 40.0 # Higher delivery fee
        return results


class MockCheapGroceryProvider(MockGoldenGroceryProvider):
    name: str = "MockCheapGrocery"
    
    async def search(self, query: str, location: Location | None = None) -> list[dict[str, Any]]:
        results = await super().search(query, location)
        
        # Cheap provider is out of stock often
        if location and location.postal_code == "CHEAP_OUT_OF_STOCK":
            for r in results:
                r["availability"] = "OUT_OF_STOCK"
                
        for r in results:
            r["price"] = round(r["price"] * 0.8, 2)  # 20% cheaper
            r["delivery_minutes"] = 30
            r["delivery_fee"] = 10.0 # Cheaper delivery
            r["discount"] = 5.0 # Random discount
        return results

