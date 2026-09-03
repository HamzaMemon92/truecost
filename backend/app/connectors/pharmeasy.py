from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class PharmEasyConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "PharmEasy"

    def _find_products(self, obj, depth=0):
        if depth > 8:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            if any(k in obj[0] for k in ["name", "productName", "mrp", "selling_price", "discountedMrp"]):
                return obj
        if isinstance(obj, dict):
            for key in ["productList", "products", "skus", "items", "data", "result", "medicines"]:
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
                if isinstance(item, (dict, list)):
                    found = self._find_products(item, depth + 1)
                    if found:
                        return found
        return []

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            items = self._find_products(raw_payload)
            for item in items[:20]:
                price = item.get("mrpToBeDisplayed", item.get("discountedMrp", item.get("selling_price", item.get("mrp", 0))))
                mrp = item.get("mrp", price)
                if not price:
                    continue
                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=float(price),
                    original_price=float(mrp) if mrp and mrp != price else None,
                    delivery_time=str(item.get("delivery_time") or item.get("deliveryTime") or ""),
                    deep_link=f"https://pharmeasy.in/online-medicine-order/{item.get('slug', item.get('id', ''))}"
                )
                tc_product = TrueCostProduct(
                    id=f"tc_pharmeasy_{item.get('id', item.get('productId', ''))}",
                    name=item.get("name", item.get("productName", "Medicine")),
                    brand=item.get("manufacturerName", item.get("brand", item.get("manufacturer", "PharmEasy"))),
                    weight_volume=item.get("unitOfMeasurement", item.get("quantity", item.get("packageForm", "1 pack"))),
                    image_url=item.get("imageUrl", item.get("image", item.get("thumbnail", ""))),
                    category="Pharmacy",
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[PharmEasyConnector] Error: {e}")
        return products
