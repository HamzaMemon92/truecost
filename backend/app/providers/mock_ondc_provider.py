import asyncio
from datetime import datetime, timezone
from typing import Any

from app.schemas.grocery import Location, CanonicalGroceryItem
from app.providers.ondc_provider import OndcNetworkProvider

class MockOndcProvider(OndcNetworkProvider):
    """
    Mock ONDC Network Provider for CI and Development.
    Simulates a synchronous network discovery returning multiple distinct sellers.
    """

    def __init__(self, timeout_ms: int = 4500):
        super().__init__(timeout_ms)
        self.name = "Mock_ONDC_Network"
        self.status = "active"
        self.source_type = "mock"

    async def search(self, query: str, location: Location | None = None) -> list[CanonicalGroceryItem] | list[dict[str, Any]]:
        # Simulate network latency
        await asyncio.sleep(0.1)

        normalized_results = []
        now = datetime.now(timezone.utc)

        # We will deterministically return results based on the query to test deduplication
        query_lower = query.lower()

        if "amul" in query_lower or "milk" in query_lower:
            # Simulate 3 different sellers returning the exact same physical product (1L)
            # They should all share the same GTIN.
            
            base_1L_product = {
                "descriptor": {"name": "Amul Taaza Toned Milk", "code": "1:amul-taaza-toned-milk-1l"}, # Shared GTIN
            }

            # Seller A: Cheapest, standard availability
            seller_a = self._normalize_ondc_item("bpp_mock_1", "seller_A", {
                **base_1L_product,
                "id": "SKU-A-101",
                "price": {"value": 68.0, "maximum_value": 70.0, "currency": "INR"},
                "quantity": {"available": {"count": 15}}
            })
            seller_a["brand"] = "Amul"
            seller_a["quantity_value"] = 1.0
            seller_a["quantity_unit"] = "L"
            
            # Seller B: More expensive, but in stock
            seller_b = self._normalize_ondc_item("bpp_mock_2", "seller_B", {
                **base_1L_product,
                "id": "ITEM-8822",
                "price": {"value": 70.0, "maximum_value": 70.0, "currency": "INR"},
                "quantity": {"available": {"count": 5}}
            })
            seller_b["brand"] = "Amul"
            seller_b["quantity_value"] = 1.0
            seller_b["quantity_unit"] = "L"

            # Seller C: Cheapest, but OUT OF STOCK
            seller_c = self._normalize_ondc_item("bpp_mock_3", "seller_C", {
                **base_1L_product,
                "id": "AML-TZ-1L",
                "price": {"value": 65.0, "maximum_value": 70.0, "currency": "INR"},
                "quantity": {"available": {"count": 0}} # 0 means OUT_OF_STOCK
            })
            seller_c["brand"] = "Amul"
            seller_c["quantity_value"] = 1.0
            seller_c["quantity_unit"] = "L"

            # Simulate 1 seller offering a DIFFERENT variant (500ml)
            seller_a_500 = self._normalize_ondc_item("bpp_mock_1", "seller_A", {
                "descriptor": {"name": "Amul Taaza Toned Milk", "code": "1:amul-taaza-toned-milk-500ml"}, # Different GTIN
                "id": "SKU-A-102",
                "price": {"value": 35.0, "maximum_value": 35.0, "currency": "INR"},
                "quantity": {"available": {"count": 20}}
            })
            seller_a_500["brand"] = "Amul"
            seller_a_500["quantity_value"] = 500.0
            seller_a_500["quantity_unit"] = "ml"

            normalized_results.extend([seller_a, seller_b, seller_c, seller_a_500])

        # Enforce mock type overrides
        for item in normalized_results:
            item["source_type"] = "mock"
            item["retrieved_at"] = now
            item["price_checked_at"] = now
            item["availability_checked_at"] = now

        return normalized_results
