from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class MyntraConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Myntra"

    def _find_products(self, obj, depth=0):
        if depth > 8:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            if any(k in obj[0] for k in ["productName", "productId", "brandName", "price", "discountedPrice"]):
                return obj
        if isinstance(obj, dict):
            for key in ["results", "products", "productList", "items", "data", "catalogue"]:
                if key in obj and isinstance(obj[key], list) and obj[key]:
                    found = self._find_products(obj[key], depth + 1)
                    if found:
                        return found
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    found = self._find_products(v, depth + 1)
                    if found:
                        return found
        if isinstance(obj, list):
            for item in obj:
                found = self._find_products(item, depth + 1)
                if found:
                    return found
        return []

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            items = self._find_products(raw_payload)
            for p in items[:15]:
                name = p.get("productName", p.get("name", "Product"))
                price_obj = p.get("price", {})
                if isinstance(price_obj, dict):
                    price = float(price_obj.get("discounted", price_obj.get("value", 0)) or 0)
                    mrp = float(price_obj.get("mrp", price) or price)
                else:
                    price = float(price_obj or p.get("discountedPrice", 0) or 0)
                    mrp = float(p.get("mrp", price) or price)
                if not price:
                    continue
                images = p.get("images", [])
                image = ""
                if isinstance(images, list) and images:
                    first = images[0]
                    image = first.get("src", first.get("secureSrc", "")) if isinstance(first, dict) else str(first)
                landing = str(p.get("landingPageUrl") or p.get("productId") or "").strip()
                if landing.startswith("http"):
                    deep_link = landing
                elif landing.startswith("/"):
                    deep_link = f"https://www.myntra.com{landing}"
                else:
                    deep_link = f"https://www.myntra.com/{landing}" if landing else "https://www.myntra.com"

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=mrp if mrp > price else None,
                    delivery_time="",
                    deep_link=deep_link
                )
                tc_product = TrueCostProduct(
                    id=f"tc_myntra_{p.get('productId', hash(name) % 999999)}",
                    name=name,
                    brand=p.get("brand", p.get("brandName", "Myntra")),
                    weight_volume="",
                    image_url=image,
                    category="Shopping",
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[MyntraConnector] Error: {e}")
        return products
