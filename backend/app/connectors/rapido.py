from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class RapidoConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Rapido"

    def _find_estimates(self, obj, depth=0):
        if depth > 8:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            if any(k in obj[0] for k in ["fare", "estimatedFare", "vehicleType", "category", "type"]):
                return obj
        if isinstance(obj, dict):
            for key in ["estimates", "rides", "data", "result", "rideOptions"]:
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

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            estimates = self._find_estimates(raw_payload)
            for ride in estimates:
                fare = ride.get("fare", ride.get("estimatedFare", ride.get("totalFare", ride.get("minFare", 0))))
                try:
                    fare = float(fare or 0)
                except (TypeError, ValueError):
                    fare = 0.0
                if not fare:
                    continue
                eta = ride.get("eta", ride.get("pickupEta", ride.get("waitTime")))
                name = str(ride.get("name", ride.get("vehicleType", ride.get("category", ride.get("type", "Bike"))))).title()
                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=fare,
                    original_price=None,
                    delivery_time=f"{eta} mins" if eta is not None else "",
                    deep_link="https://rapido.bike/"
                )
                tc_product = TrueCostProduct(
                    id=f"tc_rapido_{ride.get('vehicleType', ride.get('type', 'bike'))}",
                    name=name,
                    brand="Rapido",
                    weight_volume=f"{ride.get('capacity', 1)} seat",
                    image_url=ride.get("imageUrl", ""),
                    category="Mobility",
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[RapidoConnector] Error: {e}")
        return products
