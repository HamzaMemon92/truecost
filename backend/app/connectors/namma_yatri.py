import re
from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class NammaYatriConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Namma Yatri"

    def _parse_fare(self, raw) -> float:
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            m = re.search(r"[0-9.]+", raw.replace(",", ""))
            return float(m.group()) if m else 0.0
        return 0.0

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        """
        Namma Yatri scraper sends inline-parsed fare shape:
        { items: [{ name, price, delivery_time, link }] }
        Fall back to recursive finder for raw API shapes.
        """
        products = []
        try:
            # Primary: scraper's pre-parsed output
            items = raw_payload.get("items", [])
            if items and isinstance(items[0], dict) and "name" in items[0]:
                for item in items[:10]:
                    price = self._parse_fare(item.get("price", 0))
                    if not price:
                        continue
                    provider_price = ProviderPrice(
                        provider=self.provider_name,
                        price=price,
                        original_price=None,
                        delivery_time=str(item.get("delivery_time") or ""),
                        deep_link=item.get("link", "https://nammayatri.in/")
                    )
                    products.append(TrueCostProduct(
                        id=f"tc_ny_{item.get('name', 'ride').lower().replace(' ', '_')}",
                        name=item.get("name", "Auto"),
                        brand="Namma Yatri",
                        weight_volume="3 seats",
                        image_url="",
                        category="Mobility",
                        prices=[provider_price]
                    ))
                return products

            # Fallback: raw API recursive finder for fare estimates
            estimates = self._find_estimates(raw_payload)
            for ride in estimates[:5]:
                fare_raw = ride.get("fare", ride.get("estimatedFare",
                           ride.get("totalFare", ride.get("minFare", 0))))
                price = self._parse_fare(fare_raw)
                if not price:
                    continue
                eta = ride.get("eta", ride.get("pickupEta"))
                name = ride.get("vehicleType", ride.get("category", "Auto")).title()
                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=None,
                    delivery_time=f"{eta} mins" if eta is not None else "",
                    deep_link="https://nammayatri.in/"
                )
                products.append(TrueCostProduct(
                    id=f"tc_ny_{name.lower()}",
                    name=name,
                    brand="Namma Yatri",
                    weight_volume="3 seats",
                    image_url="",
                    category="Mobility",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[NammaYatriConnector] Error: {e}")
        return products

    def _find_estimates(self, obj, depth=0):
        if depth > 8:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            if any(k in obj[0] for k in ["fare", "estimatedFare", "vehicleType", "category"]):
                return obj
        if isinstance(obj, dict):
            for key in ["estimates", "rides", "data", "result"]:
                if key in obj and isinstance(obj[key], list) and obj[key]:
                    found = self._find_estimates(obj[key], depth + 1)
                    if found:
                        return found
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    found = self._find_estimates(v, depth + 1)
                    if found:
                        return found
        if isinstance(obj, list):
            for item in obj:
                found = self._find_estimates(item, depth + 1)
                if found:
                    return found
        return []
