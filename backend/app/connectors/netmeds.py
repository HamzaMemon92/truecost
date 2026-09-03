from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class NetmedsConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Netmeds"

    def _find_products(self, obj, depth=0):
        if depth > 8:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            if any(k in obj[0] for k in ["name", "productName", "price", "mrp", "selling_price", "product_name"]):
                return obj
        if isinstance(obj, dict):
            for key in ["products", "items", "data", "result", "medicines", "catalogue", "productList"]:
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
                price = item.get("selling_price", item.get("sellingPrice",
                         item.get("price", item.get("special_price", 0))))
                mrp = item.get("mrp", item.get("originalPrice", price))
                try:
                    price = float(price or 0)
                    mrp = float(mrp or price)
                except (TypeError, ValueError):
                    continue
                if not price:
                    continue

                name = item.get("name", item.get("product_name", item.get("productName", "Medicine")))
                slug = item.get("slug", item.get("url_key", item.get("id", "")))
                image = item.get("thumbnail", item.get("image", item.get("image_url", "")))

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=mrp if mrp != price else None,
                    delivery_time=str(item.get("deliveryTime") or item.get("delivery_time") or ""),
                    deep_link=f"https://www.netmeds.com/prescriptions/{slug}"
                )
                products.append(TrueCostProduct(
                    id=f"tc_netmeds_{item.get('id', hash(name) % 999999)}",
                    name=name,
                    brand=item.get("brand", item.get("manufacturer_name", "Netmeds")),
                    weight_volume=item.get("pack_size", item.get("quantity", "1 pack")),
                    image_url=image,
                    category="Pharmacy",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[NetmedsConnector] Error: {e}")
        return products
