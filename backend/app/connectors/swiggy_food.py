from app.connectors.stealth_client import WAFBypassClient
import re
from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class SwiggyFoodConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Swiggy Food"

    def _find_restaurants(self, obj, depth=0):
        if depth > 8:
            return []
        if isinstance(obj, list):
            results = []
            for item in obj:
                results.extend(self._find_restaurants(item, depth + 1))
            return results
        if isinstance(obj, dict):
            # Check if this looks like a restaurant info node
            if "name" in obj and ("costForTwo" in obj or "sla" in obj or "avgRatingString" in obj):
                return [obj]
            results = []
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    results.extend(self._find_restaurants(v, depth + 1))
            return results
        return []

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            restaurants = self._find_restaurants(raw_payload)
            seen_ids = set()
            for info in restaurants[:12]:
                rid = str(info.get("id", info.get("restaurantId", "")))
                if rid in seen_ids:
                    continue
                seen_ids.add(rid)

                cost = info.get("costForTwo", 0)
                if isinstance(cost, str):
                    m = re.search(r"[0-9]+", cost.replace(",", ""))
                    cost = float(m.group()) if m else 0.0
                cost = float(cost or 0)

                sla = info.get("sla", {})
                delivery_time = sla.get("deliveryTime") if isinstance(sla, dict) else None
                if delivery_time is None:
                    delivery_time = info.get("deliveryTime")

                image = info.get("cloudinaryImageId", info.get("imageId", ""))

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=cost / 2 if cost else 0,
                    original_price=None,
                    delivery_time=(f"{delivery_time} mins" if delivery_time is not None else ""),
                    deep_link=f"https://www.swiggy.com/restaurants/{rid}"
                )
                tc_product = TrueCostProduct(
                    id=f"tc_swiggy_food_{rid}",
                    name=info.get("name", "Restaurant"),
                    brand="Swiggy Food",
                    weight_volume="Per person",
                    image_url=image,
                    category="Food",
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[SwiggyFoodConnector] Error: {e}")
        return products
