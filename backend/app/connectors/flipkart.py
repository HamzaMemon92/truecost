from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice


class FlipkartConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Flipkart"

    def _find_products(self, obj, depth=0):
        if depth > 10:
            return []
        if isinstance(obj, dict):
            # Check for new window.__INITIAL_STATE__ component structure (slots / products)
            val = obj.get("value")
            act = obj.get("action")
            if isinstance(val, dict) and ("titles" in val or "pricing" in val or "productMeta" in val):
                titles = val.get("titles") or {}
                pricing = val.get("pricing") or {}
                images = val.get("images") or []
                img_url = ""
                if images and isinstance(images, list) and isinstance(images[0], dict):
                    img_url = images[0].get("imageUrl", "")
                elif images and isinstance(images, list) and isinstance(images[0], str):
                    img_url = images[0]

                if img_url:
                    img_url = img_url.replace("{@width}", "400").replace("{@height}", "400").replace("{@quality}", "70")

                act_dict = act if isinstance(act, dict) else {}
                url = act_dict.get("url", "")
                params = act_dict.get("params") or {}
                pid = ""
                if isinstance(val.get("productMeta"), dict):
                    pid = val["productMeta"].get("productId", "")
                if not pid and isinstance(params, dict):
                    pid = params.get("productId", "")

                title = titles.get("title") or titles.get("newTitle") or val.get("name") or "Flipkart Product"
                display_price = pricing.get("displayPrice") or val.get("price") or 0
                mrp_price = pricing.get("strikeOffPrice") or pricing.get("displayPrice") or display_price

                if title and display_price:
                    return [{
                        "title": title,
                        "price": display_price,
                        "mrp": mrp_price,
                        "canonicalUrl": url,
                        "imageUrl": img_url,
                        "pid": pid,
                        "brand": titles.get("superTitle") or val.get("brand") or "Flipkart"
                    }]

            # Direct product shape
            has_price = (
                "finalPrice" in obj
                or "sellingPrice" in obj
                or ("pricing" in obj and isinstance(obj.get("pricing"), dict))
                or "discountedPrice" in obj
                or "price" in obj
            )
            has_title = "title" in obj or "name" in obj or "productName" in obj
            if has_price and has_title and not any(k in obj for k in ["widgetsData", "multiWidgetState", "pageMeta"]):
                return [obj]

            results = []
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    results.extend(self._find_products(v, depth + 1))
            return results

        if isinstance(obj, list):
            results = []
            for item in obj:
                results.extend(self._find_products(item, depth + 1))
            return results
        return []

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            nodes = self._find_products(raw_payload)
            seen = set()
            for node in nodes[:25]:
                pricing = node.get("pricing") or {}
                node_price = node.get("price")
                node_mrp = node.get("mrp")

                price = 0
                if isinstance(pricing, dict):
                    final_price_obj = pricing.get("finalPrice")
                    if isinstance(final_price_obj, dict):
                        price = final_price_obj.get("value", 0)
                    elif pricing.get("displayPrice"):
                        price = pricing.get("displayPrice", 0)

                if not price:
                    selling_price_obj = node.get("sellingPrice")
                    if isinstance(selling_price_obj, dict):
                        price = selling_price_obj.get("value", 0)
                    elif node.get("discountedPrice"):
                        price = node.get("discountedPrice", 0)
                    elif isinstance(node_price, (int, float, str)):
                        price = node_price
                    elif isinstance(node_price, dict):
                        price = node_price.get("value", 0)

                mrp = price
                if isinstance(pricing, dict) and pricing.get("strikeOffPrice"):
                    mrp = pricing.get("strikeOffPrice")
                elif isinstance(pricing, dict) and isinstance(pricing.get("mrp"), dict):
                    mrp = pricing.get("mrp", {}).get("value", price)
                elif isinstance(node_mrp, (int, float, str)):
                    mrp = node_mrp
                elif isinstance(node_mrp, dict):
                    mrp = node_mrp.get("value", price)

                try:
                    price = float(price or 0)
                    mrp = float(mrp or price)
                except (TypeError, ValueError):
                    continue

                if not price or price <= 0:
                    continue

                title = str(node.get("title") or node.get("name") or node.get("productName") or "Product").strip()
                pid = str(node.get("pid") or node.get("id") or (hash(title) % 999999))
                if pid in seen:
                    continue
                seen.add(pid)

                images = node.get("images") or []
                image = node.get("imageUrl") or (images[0] if isinstance(images, list) and images else "")
                if isinstance(image, dict):
                    image = image.get("imageUrl") or image.get("url", "")

                image_str = str(image or "")
                if image_str:
                    image_str = image_str.replace("{@width}", "400").replace("{@height}", "400").replace("{@quality}", "70")

                deep_link = str(node.get('canonicalUrl') or node.get('productUrl') or node.get('url') or '').strip()
                if deep_link and not deep_link.startswith('http'):
                    deep_link = f"https://www.flipkart.com{deep_link}"

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=mrp if mrp > price else None,
                    delivery_time=str(node.get("deliveryTime") or node.get("delivery_time") or ""),
                    deep_link=deep_link or "https://www.flipkart.com"
                )
                tc_product = TrueCostProduct(
                    id=f"tc_fk_{pid}",
                    name=title,
                    brand=str(node.get("brand") or "Flipkart"),
                    weight_volume="",
                    image_url=image_str,
                    category="Shopping",
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[FlipkartConnector] Error: {e}")
        return products
