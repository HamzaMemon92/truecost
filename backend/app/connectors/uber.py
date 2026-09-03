from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice

class UberConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Uber"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        """Parses Uber ride estimate data.

        Handles two payload formats:
          Format A (official Uber API): { "prices": [{"display_name", "low_estimate", ...}] }
          Format B (mobile scraper):    { "rides":  [{"name", "fare": {"amount"}, "eta_seconds", ...}] }
        """
        products = []
        try:
            # Format A: official Uber /estimates/price
            for ride in raw_payload.get("prices", []):
                low = float(ride.get("low_estimate") or 0)
                if not low:
                    continue
                high = float(ride.get("high_estimate") or low)
                dur = ride.get("duration")
                eta_str = f"{int(dur) // 60} mins" if isinstance(dur, (int, float)) else ""
                products.append(TrueCostProduct(
                    id=f"tc_uber_{ride.get('product_id', ride.get('display_name', ''))}",
                    name=ride.get("display_name", "Uber"),
                    brand="Uber",
                    weight_volume=f"{ride.get('capacity', 4)} seats",
                    image_url=ride.get("image", ""),
                    category="Mobility",
                    prices=[ProviderPrice(
                        provider=self.provider_name, price=low, original_price=high,
                        delivery_time=eta_str, deep_link="uber://?action=setPickup"
                    )]
                ))

            # Format B: mobile WebView scraper
            for ride in raw_payload.get("rides", []):
                fare_obj = ride.get("fare", {})
                price = float(fare_obj.get("amount") or fare_obj.get("price") or 0)
                if not price:
                    continue
                eta_secs = ride.get("eta_seconds", 0)
                eta_str = f"{int(eta_secs) // 60} mins" if eta_secs else ride.get("eta", "")
                products.append(TrueCostProduct(
                    id=f"tc_uber_{ride.get('id', ride.get('name', ''))}",
                    name=ride.get("name", ride.get("display_name", "Uber")),
                    brand="Uber",
                    weight_volume=f"{ride.get('capacity', 4)} seats",
                    image_url=ride.get("image_url", ""),
                    category="Mobility",
                    prices=[ProviderPrice(
                        provider=self.provider_name, price=price, original_price=price,
                        delivery_time=eta_str,
                        deep_link=ride.get("deep_link", "uber://?action=setPickup")
                    )]
                ))
        except Exception as e:
            print(f"[UberConnector] Error: {e}")
        return products
