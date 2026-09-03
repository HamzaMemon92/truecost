from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class MeeshoConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Meesho"

    def _find_products(self, obj, depth=0):
        if depth > 8:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            if any(k in obj[0] for k in ["productName", "product_name", "discountedPrice", "selling_price", "name", "min_catalog_price"]):
                return obj
        if isinstance(obj, dict):
            for key in ["products", "productList", "items", "data", "result", "catalogue", "catalogs"]:
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
                name = p.get("productName", p.get("product_name", p.get("name", "Product")))
                price = float(p.get("discountedPrice", p.get("selling_price", p.get("price", p.get("min_catalog_price", p.get("min_product_price", 0))))) or 0)
                mrp = float(p.get("mrp", p.get("original_price", price)) or price)
                if not price:
                    continue
                images = p.get("images", p.get("productImages", []))
                image = p.get("image", "")
                if not image and isinstance(images, list) and images:
                    first = images[0]
                    image = first.get("src", first.get("url", str(first))) if isinstance(first, dict) else str(first)
                elif not image and isinstance(images, str):
                    image = images
                    
                pid = str(p.get('id', p.get('hero_pid', hash(name) % 999999)))
                slug = str(p.get("slug") or pid).strip()
                if slug.startswith("http"):
                    deep_link = slug
                elif slug.startswith("/"):
                    deep_link = f"https://meesho.com{slug}"
                else:
                    deep_link = f"https://meesho.com/p/{slug}" if slug else "https://meesho.com"

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=mrp if mrp > price else None,
                    delivery_time="",
                    deep_link=deep_link
                )
                tc_product = TrueCostProduct(
                    id=f"tc_meesho_{pid}",
                    name=name,
                    brand=p.get("brand", p.get("supplier", {}).get("name", "Meesho") if isinstance(p.get("supplier"), dict) else "Meesho"),
                    weight_volume="",
                    image_url=image,
                    category="Shopping",
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[MeeshoConnector] Error: {e}")
        return products
