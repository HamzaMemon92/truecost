from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class Apollo247Connector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Apollo 247"

    def _find_products(self, obj, depth=0):
        if depth > 8:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            if any(k in obj[0] for k in ["name", "productName", "price", "mrp", "sellingPrice", "special_price"]):
                return obj
        if isinstance(obj, dict):
            # GraphQL shape: data.searchProducts.products or data.searchMedicines
            for key in ["products", "medicines", "skus", "items", "data", "result", "productList",
                        "searchProducts", "searchMedicines"]:
                if key in obj and isinstance(obj[key], (list, dict)):
                    v = obj[key]
                    if isinstance(v, list) and v:
                        found = self._find_products(v, depth + 1)
                        if found:
                            return found
                    elif isinstance(v, dict):
                        found = self._find_products(v, depth + 1)
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
                price = item.get("special_price", item.get("sellingPrice",
                         item.get("price", item.get("discountedPrice", 0))))
                mrp = item.get("price", item.get("mrp", price))
                try:
                    price = float(price or 0)
                    mrp = float(mrp or price)
                except (TypeError, ValueError):
                    continue
                if not price:
                    continue

                name = item.get("name", item.get("productName", item.get("medicineName", "Medicine")))
                slug = item.get("slug", item.get("urlKey", item.get("id", "")))
                image = item.get("thumbnail", item.get("image", item.get("imageUrl", "")))

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=mrp if mrp != price else None,
                    delivery_time=str(item.get("deliveryTime") or ""),
                    deep_link=f"https://www.apollo247.com/medicines/{slug}"
                )
                products.append(TrueCostProduct(
                    id=f"tc_apollo247_{item.get('id', hash(name) % 999999)}",
                    name=name,
                    brand=item.get("brand", item.get("manufacturer", "Apollo")),
                    weight_volume=item.get("packSize", item.get("quantity", item.get("unit", "1 strip"))),
                    image_url=image,
                    category="Pharmacy",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[Apollo247Connector] Error: {e}")
        return products
