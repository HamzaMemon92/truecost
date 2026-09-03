import re
from urllib.parse import quote_plus
from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice

def _slug(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").casefold()).strip("-")
    return text or "product"

def _bigbasket_link(product_id: Any, name: Any) -> str:
    pid = str(product_id or "").strip()
    if pid:
        return f"https://www.bigbasket.com/pd/{pid}/{_slug(name)}/"
    return f"https://www.bigbasket.com/ps/?q={quote_plus(str(name or '').strip())}"

def _bigbasket_search(name: Any) -> str:
    return f"https://www.bigbasket.com/ps/?q={quote_plus(str(name or '').strip())}"

class BigBasketConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "BigBasket"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            items = []
            def extract_items(node):
                if isinstance(node, dict):
                    if "products" in node and isinstance(node["products"], list):
                        items.extend(node["products"])
                    for v in node.values():
                        extract_items(v)
                elif isinstance(node, list):
                    for i in node:
                        extract_items(i)
            
            extract_items(raw_payload)

            for item in items:
                # new format
                if "pricing" in item and "discount" in item["pricing"]:
                    discount = item["pricing"]["discount"]
                    price = discount.get("prim_price", {}).get("sp", discount.get("mrp", 0))
                    mrp = discount.get("mrp", price)
                else:
                    # fallback to old
                    aps = item.get("aps", {})
                    price = aps.get("sp", aps.get("cp", 0))
                    mrp = aps.get("mrp", price)

                if not price:
                    continue

                product_name = item.get("desc", item.get("description", "Unknown"))
                availability = item.get("availability", {}) if isinstance(item.get("availability"), dict) else {}
                product_url = item.get("absolute_url") or item.get("url") or _bigbasket_link(item.get("id", ""), product_name)
                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=float(price),
                    original_price=float(mrp),
                    delivery_time=availability.get("short_eta", ""),
                    deep_link=product_url,
                    product_url=product_url if str(product_url).startswith("http") else None,
                    fallback_search_url=_bigbasket_search(product_name),
                    handoff_confidence="exact_product" if item.get("id") else "search",
                    in_stock=availability.get("avail_status") == "001" if availability.get("avail_status") is not None else None,
                    serviceable=availability.get("availability_status") == "available" if availability.get("availability_status") is not None else None,
                )

                images = item.get("images", [])
                image_url = ""
                if images and isinstance(images, list) and isinstance(images[0], dict):
                    image_url = images[0].get("m", images[0].get("s", ""))
                elif item.get("ib", {}).get("m"):
                    image_url = item.get("ib", {}).get("m")

                tc_product = TrueCostProduct(
                    id=f"tc_bigbasket_{item.get('id', '')}",
                    name=product_name,
                    brand=item.get("brand", {}).get("name", "BigBasket") if isinstance(item.get("brand"), dict) else str(item.get("brand", "")),
                    weight_volume=item.get("w", item.get("pack_desc", "1 unit")),
                    image_url=image_url,
                    category="Grocery",
                    provider_sku=str(item.get("id", "")),
                    unknown_attributes={
                        "image_match_status": "EXACT_SKU_IMAGE" if image_url else "NO_IMAGE",
                        "image_source_provider": self.provider_name if image_url else None,
                        "image_source_product_id": item.get("id"),
                        "image_source_variant_id": item.get("id"),
                    },
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[BigBasketConnector] Parsing Error: {e}")
        return products
