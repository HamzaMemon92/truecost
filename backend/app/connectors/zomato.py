import re
from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class ZomatoConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Zomato"

    def _find_restaurants(self, obj, depth=0):
        if depth > 10:
            return []
        if isinstance(obj, dict):
            # Looks like a restaurant info node
            if "name" in obj and ("costForTwo" in obj or "costForTwoMessage" in obj or "avgRating" in obj):
                return [obj]
            results = []
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    results.extend(self._find_restaurants(v, depth + 1))
            return results
        if isinstance(obj, list):
            results = []
            for item in obj:
                results.extend(self._find_restaurants(item, depth + 1))
            return results
        return []

    def _parse_cost(self, cost) -> float:
        if isinstance(cost, (int, float)):
            return float(cost)
        if isinstance(cost, str):
            m = re.search(r"[0-9,]+", cost.replace(",", ""))
            return float(m.group()) if m else 0.0
        return 0.0

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            restaurants = self._find_restaurants(raw_payload)
            seen_ids = set()
            for info in restaurants[:12]:
                rid = str(info.get("id", info.get("resId", "")))
                if rid in seen_ids:
                    continue
                seen_ids.add(rid)

                cost_raw = info.get("costForTwo", info.get("costForTwoMessage", 0))
                cost = self._parse_cost(cost_raw)

                sla = info.get("sla", {})
                delivery_time = None
                if isinstance(sla, dict):
                    delivery_time = sla.get("deliveryTime", sla.get("lastMileTravelString"))
                if delivery_time is None:
                    delivery_time = info.get("deliveryTime")

                image = info.get("thumbnail", info.get("cloudinaryImageId", info.get("featuredImage", "")))

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=cost / 2 if cost else 0,
                    original_price=None,
                    delivery_time=(f"{delivery_time} mins" if delivery_time is not None else ""),
                    deep_link=f"https://www.zomato.com/order-food-online"
                )
                tc_product = TrueCostProduct(
                    id=f"tc_zomato_{rid}",
                    name=info.get("name", "Restaurant"),
                    brand="Zomato",
                    weight_volume="Per person",
                    image_url=image,
                    category="Food",
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[ZomatoConnector] Error: {e}")
        return products
