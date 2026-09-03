from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


def _find_flights(obj, depth=0):
    if depth > 8:
        return []
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        if any(k in obj[0] for k in ["fare", "totalFare", "airlineName", "segments", "airline", "duration"]):
            return obj
    if isinstance(obj, dict):
        for key in ["results", "itineraries", "flights", "trips", "data", "flightResults", "searchResult"]:
            if key in obj and isinstance(obj[key], list) and obj[key]:
                found = _find_flights(obj[key], depth + 1)
                if found:
                    return found
        for v in obj.values():
            if isinstance(v, (dict, list)):
                found = _find_flights(v, depth + 1)
                if found:
                    return found
    if isinstance(obj, list):
        for item in obj:
            found = _find_flights(item, depth + 1)
            if found:
                return found
    return []


class CleartripConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Cleartrip"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            results = _find_flights(raw_payload)
            seen = set()
            for item in results[:10]:
                fare = item.get("fare", item.get("totalFare", item.get("price", {})))
                if isinstance(fare, dict):
                    price = float(fare.get("totalFare", fare.get("publishedFare",
                                  fare.get("amount", fare.get("value", 0)))) or 0)
                else:
                    try:
                        price = float(fare or 0)
                    except (TypeError, ValueError):
                        price = 0.0
                if not price:
                    continue

                airline = item.get("name", item.get("flightName", item.get("airlineName", item.get("airline", ""))))
                if not airline:
                    segs = item.get("segments", [{}])
                    if segs and isinstance(segs[0], dict):
                        al = segs[0].get("airline", {})
                        airline = al.get("name", "") if isinstance(al, dict) else str(al)
                airline = airline or "Flight"

                rid = str(item.get("id", item.get("resultIndex", hash(airline) % 999999)))
                if rid in seen:
                    continue
                seen.add(rid)
                duration = item.get("duration", item.get("totalDuration", ""))

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=None,
                    delivery_time=str(duration),
                    deep_link="https://www.cleartrip.com/flights/"
                )
                tc_product = TrueCostProduct(
                    id=f"tc_cleartrip_{rid}",
                    name=airline,
                    brand="Cleartrip",
                    weight_volume=str(duration),
                    image_url="",
                    category="Travel",
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[CleartripConnector] Error: {e}")
        return products
