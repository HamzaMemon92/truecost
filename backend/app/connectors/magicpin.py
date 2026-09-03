import re
from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class MagicPinConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "MagicPin"

    def _find_merchants(self, obj, depth=0):
        if depth > 8:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            if any(k in obj[0] for k in ["merchantName", "name", "avgCostForTwo", "costForTwo", "merchantId"]):
                return obj
        if isinstance(obj, dict):
            for key in ["merchants", "items", "data", "result", "searchResults", "restaurants"]:
                if key in obj and isinstance(obj[key], list) and obj[key]:
                    found = self._find_merchants(obj[key], depth + 1)
                    if found:
                        return found
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    found = self._find_merchants(v, depth + 1)
                    if found:
                        return found
        if isinstance(obj, list):
            for item in obj:
                found = self._find_merchants(item, depth + 1)
                if found:
                    return found
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
            merchants = self._find_merchants(raw_payload)
            seen = set()
            for m in merchants[:12]:
                mid = str(m.get("merchantId", m.get("id", "")))
                if mid in seen:
                    continue
                seen.add(mid)

                cost_raw = m.get("avgCostForTwo", m.get("costForTwo", m.get("minOrderValue", 0)))
                cost = self._parse_cost(cost_raw)
                name = m.get("merchantName", m.get("name", "Restaurant"))
                image = m.get("imageUrl", m.get("image", m.get("coverImage", "")))
                slug = m.get("merchantSlug", m.get("slug", mid))

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=cost / 2 if cost else 0,
                    original_price=None,
                    delivery_time=str(m.get("deliveryTime", m.get("eta", "")) or ""),
                    deep_link=f"https://magicpin.in/offers/{slug}/"
                )
                products.append(TrueCostProduct(
                    id=f"tc_magicpin_{mid}",
                    name=name,
                    brand="MagicPin",
                    weight_volume="Per person",
                    image_url=image,
                    category="Food",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[MagicPinConnector] Error: {e}")
        return products
