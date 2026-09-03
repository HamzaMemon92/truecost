from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class MakeMyTripConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "MakeMyTrip"

    def _find_itineraries(self, obj, depth=0):
        if depth > 8:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            if any(k in obj[0] for k in ["fare", "totalFare", "airlineName", "segments", "airline"]):
                return obj
        if isinstance(obj, dict):
            for key in ["results", "itineraries", "flights", "trips", "data", "flightResults"]:
                if key in obj and isinstance(obj[key], list) and obj[key]:
                    found = self._find_itineraries(obj[key], depth + 1)
                    if found:
                        return found
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    found = self._find_itineraries(v, depth + 1)
                    if found:
                        return found
        if isinstance(obj, list):
            for item in obj:
                found = self._find_itineraries(item, depth + 1)
                if found:
                    return found
        return []

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            results = self._find_itineraries(raw_payload)
            for item in results[:10]:
                # Extract fare
                fare_obj = item.get("fare", item.get("totalFare", item.get("price", {})))
                if isinstance(fare_obj, dict):
                    price = fare_obj.get("totalFareWithoutConvFee",
                                         fare_obj.get("published",
                                         fare_obj.get("netFare",
                                         fare_obj.get("amount", 0))))
                else:
                    price = float(fare_obj or 0)

                try:
                    price = float(price or 0)
                except (TypeError, ValueError):
                    price = 0.0
                if not price:
                    continue

                # Extract airline name
                airline = item.get("name", item.get("flightName", item.get("airlineName", item.get("airline", ""))))
                if not airline:
                    segs = item.get("segments", [{}])
                    if segs and isinstance(segs[0], dict):
                        al = segs[0].get("airline", {})
                        if isinstance(al, dict):
                            airline = al.get("airlineName", al.get("name", "Flight"))
                        else:
                            airline = str(al)
                airline = airline or "Flight"

                duration = item.get("duration", item.get("totalDuration", item.get("tripDuration", "")))

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=None,
                    delivery_time=str(duration),
                    deep_link="https://www.makemytrip.com/flights/"
                )
                tc_product = TrueCostProduct(
                    id=f"tc_mmt_{item.get('id', item.get('resultIndex', hash(airline) % 999999))}",
                    name=airline,
                    brand="MakeMyTrip",
                    weight_volume=str(duration),
                    image_url="",
                    category="Travel",
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[MakeMyTripConnector] Error: {e}")
        return products
