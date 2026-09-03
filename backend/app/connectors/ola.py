import re
from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class OlaConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Ola"

    def _parse_price(self, raw) -> float:
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            m = re.search(r"[0-9.]+", raw.replace(",", ""))
            return float(m.group()) if m else 0.0
        return 0.0

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            # Ola v2 API: serviceTypes[]
            # Ola v1 API: ride_estimate.categories[]
            service_types = (
                raw_payload.get("serviceTypes", [])
                or raw_payload.get("ride_estimate", {}).get("categories", [])
                or raw_payload.get("categories", [])
                or raw_payload.get("rides", [])
            )
            for ride in service_types:
                # v2 shape: {id, name, pricing: {currencyAmount, minimumFare}, eta, maxPassengers}
                pricing = ride.get("pricing", {})
                price_raw = pricing.get("currencyAmount", pricing.get("minimumFare", 0))
                # v1 shape: {id, display_name, price_descriptor: {formatted_content: "₹80-120"}, eta, capacity}
                if not price_raw:
                    price_desc = ride.get("price_descriptor", {})
                    price_str = price_desc.get("formatted_content", "0").replace("₹", "").split("-")[0].strip()
                    price_raw = price_str

                price = self._parse_price(price_raw)
                eta = ride.get("eta", ride.get("pickupEta"))

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=None,
                    delivery_time=f"{eta} mins" if eta is not None else "",
                    deep_link="ola://"
                )
                tc_product = TrueCostProduct(
                    id=f"tc_ola_{ride.get('id', ride.get('name', ''))}",
                    name=ride.get("name", ride.get("display_name", "Ola")),
                    brand="Ola",
                    weight_volume=f"{ride.get('maxPassengers', ride.get('capacity', 4))} seats",
                    image_url=ride.get("imageUrl", ride.get("image", "")),
                    category="Mobility",
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[OlaConnector] Error: {e}")
        return products
