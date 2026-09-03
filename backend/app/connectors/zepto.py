import re
from urllib.parse import quote_plus
from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice

def _slug(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").casefold()).strip("-")
    return text or "product"

def _zepto_link(product: Dict[str, Any], variant: Dict[str, Any]) -> str:
    name = product.get("name") or "product"
    variant_id = variant.get("id") or variant.get("productVariantId") or variant.get("product_variant_id")
    if variant_id:
        return f"https://www.zepto.com/pn/{_slug(name)}/pvid/{variant_id}"
    return f"https://www.zepto.com/search?query={quote_plus(str(name).strip())}"

def _zepto_search(name: Any) -> str:
    return f"https://www.zepto.com/search?query={quote_plus(str(name or '').strip())}"

def _to_rupees(value: Any) -> float:
    amount = float(value or 0)
    # Zepto captured payloads vary between paise integers and rupee values.
    return amount / 100 if amount > 999 else amount

def _first_text(item: Dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = value.get("text") or value.get("value") or value.get("name")
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
    return ""

def _flat_availability(item: Dict[str, Any]) -> bool | None:
    for key in ("in_stock", "inStock", "available", "isAvailable", "serviceable", "isServiceable"):
        value = item.get(key)
        if isinstance(value, bool):
            return value
    text = " ".join(str(item.get(key) or "") for key in ("availability", "stock", "status"))
    if re.search(r"out|sold|unavailable|notify", text, flags=re.I):
        return False
    if re.search(r"available|add|in stock", text, flags=re.I):
        return True
    return None

class ZeptoConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Zepto"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            flat_products = raw_payload.get("products", [])
            if flat_products and isinstance(flat_products[0], dict):
                seen = set()
                for item in flat_products[:40]:
                    price = _to_rupees(item.get("sp") or item.get("price") or item.get("sellingPrice") or 0)
                    if not price:
                        continue
                    name = _first_text(item, ("name", "title", "display_name", "displayName", "product_name", "productName"))
                    if not name:
                        continue
                    nav_id = str(item.get("nav_id") or item.get("id") or item.get("variant_id") or item.get("variantId") or name)
                    unit = _first_text(item, ("unit", "weight", "weightVolume", "weight_volume", "pack_size", "packSize", "formattedPacksize")) or "1 unit"
                    dedupe_key = f"{nav_id}|{name}|{unit}|{price}".casefold()
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    product_url = item.get("url") or item.get("product_url") or item.get("productUrl") or _zepto_search(name)
                    image_url = item.get("img_url") or item.get("image_url") or item.get("imageUrl") or ""
                    in_stock = _flat_availability(item)
                    provider_price = ProviderPrice(
                        provider=self.provider_name,
                        price=price,
                        original_price=_to_rupees(item.get("mrp") or item.get("original_price") or price),
                        delivery_time=item.get("delivery_time", ""),
                        deep_link=product_url,
                        product_url=product_url if str(product_url).startswith("http") else None,
                        fallback_search_url=_zepto_search(name),
                        handoff_confidence="exact_product" if nav_id and nav_id != name else "search",
                        in_stock=in_stock,
                        serviceable=item.get("serviceable") if isinstance(item.get("serviceable"), bool) else None,
                    )
                    products.append(TrueCostProduct(
                        id=f"tc_zepto_{_slug(nav_id)}",
                        name=name,
                        brand=item.get("brand", "Zepto"),
                        weight_volume=unit,
                        image_url=image_url,
                        category="Grocery",
                        provider_sku=nav_id,
                        unknown_attributes={
                            "image_match_status": "EXACT_SKU_IMAGE" if image_url else "NO_IMAGE",
                            "image_source_provider": self.provider_name if image_url else None,
                            "image_source_product_id": nav_id,
                            "image_source_variant_id": nav_id,
                        },
                        prices=[provider_price],
                    ))
                return products

            # Zepto uses "layout" for UI blocks
            layout_blocks = raw_payload.get("layout", [])
            
            items_array = []
            for block in layout_blocks:
                if block.get("widgetId") == "PRODUCT_GRID":
                    items = block.get("data", {}).get("resolver", {}).get("data", {}).get("items", [])
                    items_array.extend(items)
            
            for item in items_array:
                # The data is inside productResponse
                pr = item.get("productResponse")
                if not pr:
                    continue
                
                product_info = pr.get("product", {})
                variant_info = pr.get("productVariant", {})
                
                price = _to_rupees(pr.get("sellingPrice", 0))
                mrp = _to_rupees(pr.get("mrp", 0))
                
                if not price:
                    continue
                    
                product_url = pr.get("productUrl") or pr.get("url") or _zepto_link(product_info, variant_info)
                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=mrp,
                    delivery_time=item.get("delivery_time", ""),
                    deep_link=product_url,
                    product_url=product_url if str(product_url).startswith("http") else None,
                    fallback_search_url=_zepto_search(product_info.get("name", "")),
                    handoff_confidence="exact_product" if variant_info.get("id") or variant_info.get("productVariantId") else "search",
                    in_stock=pr.get("inStock") if isinstance(pr.get("inStock"), bool) else None,
                    serviceable=pr.get("isServiceable") if isinstance(pr.get("isServiceable"), bool) else None,
                )
                
                # Extract image path
                image_url = ""
                images = variant_info.get("images", [])
                if images and images[0].get("path"):
                    # Zepto CDN is usually https://cdn.zeptonow.com/
                    image_url = "https://cdn.zeptonow.com/" + images[0].get("path")
                
                tc_product = TrueCostProduct(
                    id=f"tc_zepto_{pr.get('id')}",
                    name=product_info.get("name", "Unknown"),
                    brand=product_info.get("brand", "Unknown"),
                    weight_volume=variant_info.get("formattedPacksize", "1 unit"),
                    image_url=image_url,
                    category="Grocery",
                    provider_sku=str(variant_info.get("id") or variant_info.get("productVariantId") or pr.get("id") or ""),
                    unknown_attributes={
                        "image_match_status": "EXACT_SKU_IMAGE" if image_url else "NO_IMAGE",
                        "image_source_provider": self.provider_name if image_url else None,
                        "image_source_product_id": product_info.get("id") or pr.get("id"),
                        "image_source_variant_id": variant_info.get("id") or variant_info.get("productVariantId") or pr.get("id"),
                    },
                    prices=[provider_price]
                )
                products.append(tc_product)
                
        except Exception as e:
            print(f"[ZeptoConnector] Parsing Error: {e}")
            
        return products
