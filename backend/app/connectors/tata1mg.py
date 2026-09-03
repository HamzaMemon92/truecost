from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class Tata1mgConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Tata 1mg"

    def _find_products(self, obj, depth=0):
        if depth > 8:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            # Looks like a product list if items have name + price fields
            if any(k in obj[0] for k in ["name", "productName", "selling_price", "mrp", "price"]):
                return obj
        if isinstance(obj, dict):
            for key in ["skus", "products", "productList", "items", "result", "data"]:
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
            for item in items[:20]:
                price = item.get("selling_price", item.get("price", item.get("discountedPrice", 0)))
                mrp = item.get("mrp", price)
                if not price:
                    continue
                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=float(price),
                    original_price=float(mrp) if mrp and mrp != price else None,
                    delivery_time=str(item.get("delivery_time") or item.get("deliveryTime") or ""),
                    deep_link=f"https://www.1mg.com/drugs/{item.get('slug', item.get('urlKey', ''))}"
                )
                tc_product = TrueCostProduct(
                    id=f"tc_1mg_{item.get('id', item.get('sku_id', ''))}",
                    name=item.get("name", item.get("productName", "Medicine")),
                    brand=item.get("manufacturer_name", item.get("brand", item.get("manufacturerName", "1mg"))),
                    weight_volume=item.get("pack_size", item.get("unit_of_measurement", item.get("packagingInfo", "1 strip"))),
                    image_url=item.get("image", item.get("imageUrl", item.get("thumbnail", ""))),
                    category="Pharmacy",
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[Tata1mgConnector] Error: {e}")
        return products
