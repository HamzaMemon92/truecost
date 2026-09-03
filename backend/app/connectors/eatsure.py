import re
from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class EatSureConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "EatSure"

    def _find_restaurants(self, obj, depth=0):
        if depth > 8:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            if any(k in obj[0] for k in ["name", "restaurantName", "costForTwo", "minOrderValue", "restaurantId"]):
                return obj
        if isinstance(obj, dict):
            for key in ["restaurants", "items", "data", "result", "searchResults"]:
                if key in obj and isinstance(obj[key], list) and obj[key]:
                    found = self._find_restaurants(obj[key], depth + 1)
                    if found:
                        return found
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    found = self._find_restaurants(v, depth + 1)
                    if found:
                        return found
        if isinstance(obj, list):
            for item in obj:
                found = self._find_restaurants(item, depth + 1)
                if found:
                    return found
        return []

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            restaurants = self._find_restaurants(raw_payload)
            seen = set()
            for r in restaurants[:12]:
                rid = str(r.get("restaurantId", r.get("id", "")))
                if rid in seen:
                    continue
                seen.add(rid)

                cost_raw = r.get("costForTwo", r.get("minOrderValue", r.get("avgCost", 0)))
                try:
                    cost = float(cost_raw or 0)
                except (TypeError, ValueError):
                    cost = 0.0

                name = r.get("restaurantName", r.get("name", "Restaurant"))
                image = r.get("imageUrl", r.get("thumbnail", r.get("image", "")))
                eta = r.get("deliveryTime", r.get("eta"))

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=cost / 2 if cost else 0,
                    original_price=None,
                    delivery_time=f"{eta} mins" if eta is not None else "",
                    deep_link=f"https://www.eatsure.com/order/{rid}"
                )
                products.append(TrueCostProduct(
                    id=f"tc_eatsure_{rid}",
                    name=name,
                    brand="EatSure",
                    weight_volume="Per person",
                    image_url=image,
                    category="Food",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[EatSureConnector] Error: {e}")
        return products
