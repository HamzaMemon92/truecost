from typing import List, Dict, Any
import re
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class AmazonConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Amazon"

    def _parse_price(self, raw) -> float:
        """Handles prices like '1,299', '₹1299', 1299, 1299.0"""
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            cleaned = re.sub(r"[₹,\s]", "", raw)
            m = re.search(r"[0-9]+\.?[0-9]*", cleaned)
            return float(m.group()) if m else 0.0
        return 0.0

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            # Primary: DOM-parsed shape from AmazonScraper fallback
            # { amazonData: [{name, price, image, url}] }
            amazon_data = raw_payload.get("amazonData", [])
            if amazon_data:
                for item in amazon_data[:15]:
                    price = self._parse_price(item.get("price", 0))
                    if not price:
                        continue
                    provider_price = ProviderPrice(
                        provider=self.provider_name,
                        price=price,
                        original_price=None,
                        delivery_time="",
                        deep_link=item.get("url", "https://www.amazon.in/")
                    )
                    products.append(TrueCostProduct(
                        id=f"tc_amazon_{hash(item.get('name', '')) % 999999}",
                        name=item.get("name", "Amazon Product"),
                        brand="Amazon",
                        weight_volume="",
                        image_url=item.get("image", ""),
                        category="Shopping",
                        prices=[provider_price]
                    ))
                return products

            # Fallback: API shape { items: [...] }
            for item in raw_payload.get("items", [])[:15]:
                price = self._parse_price(item.get("price", 0))
                if not price:
                    continue
                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    delivery_time=str(item.get("delivery_time") or ""),
                    deep_link=item.get("url", "https://www.amazon.in/")
                )
                products.append(TrueCostProduct(
                    id=f"tc_amazon_{hash(item.get('name', '')) % 999999}",
                    name=item.get("name", "Amazon Product"),
                    brand="Amazon",
                    weight_volume="",
                    image_url=item.get("image_url", ""),
                    category="Shopping",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[AmazonConnector] Error: {e}")
        return products
