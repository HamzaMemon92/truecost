from app.connectors.stealth_client import WAFBypassClient
import re
from urllib.parse import quote_plus
from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice

def _swiggy_instamart_link(sku_id: Any, name: Any) -> str:
    sku = str(sku_id or "").strip()
    if sku:
        return f"https://www.swiggy.com/instamart/item/{sku}"
    return f"https://www.swiggy.com/instamart/search?custom_back=true&query={quote_plus(str(name or '').strip())}"

def _swiggy_instamart_search(name: Any) -> str:
    return f"https://www.swiggy.com/instamart/search?custom_back=true&query={quote_plus(str(name or '').strip())}"

def _as_float(value: Any, *, paise: bool = False) -> float:
    if isinstance(value, dict):
        for key in ("units", "value", "amount", "price", "sp"):
            if key in value:
                return _as_float(value.get(key), paise=paise)
        return 0.0
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    return number / 100 if paise and number > 999 else number

def _price_from(item: Dict[str, Any]) -> tuple[float, float]:
    price_info = item.get("price", {})
    if isinstance(price_info, dict):
        offer = (
            _as_float(price_info.get("offerPrice"))
            or _as_float(price_info.get("offer_price"), paise=True)
            or _as_float(price_info.get("finalPrice"))
            or _as_float(price_info.get("sellingPrice"))
            or _as_float(price_info.get("price"), paise=True)
        )
        mrp = (
            _as_float(price_info.get("mrp"))
            or _as_float(price_info.get("listPrice"))
            or offer
        )
        return offer, mrp

    offer = (
        _as_float(item.get("sp"))
        or _as_float(item.get("sellingPrice"), paise=True)
        or _as_float(item.get("offerPrice"), paise=True)
        or _as_float(item.get("price"), paise=True)
    )
    mrp = _as_float(item.get("mrp"), paise=True) or offer
    return offer, mrp

def _text_from(item: Dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = item.get(key)
        if value not in (None, "", [], {}):
            return str(value).strip()
    return ""

def _looks_like_size(value: str) -> bool:
    return bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:ml|l|lt|ltr|litre|liter|g|kg|pc|pcs|pack)\b", value.casefold()))

def _first_image_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("url", "imageUrl", "image_url", "path", "id"):
            nested = _first_image_value(value.get(key))
            if nested:
                return nested
    if isinstance(value, list):
        for item in value:
            nested = _first_image_value(item)
            if nested:
                return nested
    return ""

def _swiggy_image_url(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return ""
    if value.startswith("http"):
        return value
    return f"https://instamart-media-assets.swiggy.com/swiggy/image/upload/{value}"

def _image_url_from_node(node: Dict[str, Any]) -> str:
    direct = _first_image_value(node.get("imageUrl") or node.get("image_url") or node.get("img_url") or node.get("image"))
    if direct:
        return _swiggy_image_url(direct)
    image_id = _first_image_value(node.get("imageIds") or node.get("image_ids"))
    return _swiggy_image_url(image_id)

def _variant_nodes(item: Dict[str, Any]) -> list[Dict[str, Any]]:
    variant_keys = {
        "variants",
        "variations",
        "variationList",
        "variantList",
        "skuVariants",
        "productVariants",
        "product_variants",
        "options",
        "productOptions",
    }
    found: list[Dict[str, Any]] = []

    def walk(node: Any, *, under_variant_key: bool = False) -> None:
        if isinstance(node, dict):
            price, _ = _price_from(node)
            size = _text_from(node, ("quantityDescription", "quantity", "unit", "weight", "packSize", "formattedPacksize", "displayName", "name", "label", "title"))
            if under_variant_key and (price or _looks_like_size(size)):
                found.append(node)
            for key, value in node.items():
                walk(value, under_variant_key=under_variant_key or key in variant_keys)
        elif isinstance(node, list):
            for child in node:
                walk(child, under_variant_key=under_variant_key)

    walk(item)
    return found

def _expanded_items(item: Dict[str, Any]) -> list[Dict[str, Any]]:
    variants = _variant_nodes(item)
    if not variants:
        image_url = _image_url_from_node(item)
        if image_url:
            item = {
                **item,
                "_tc_image_url": image_url,
                "_tc_image_match_status": "EXACT_SKU_IMAGE",
                "_tc_image_source_scope": "product",
            }
        return [item]

    expanded = []
    base_name = _text_from(item, ("displayName", "name", "productName", "title")) or "Unknown"
    parent_image_url = _image_url_from_node(item)
    for variant in variants:
        price, _ = _price_from(variant)
        if not price:
            continue
        merged = {**item, **variant}
        variant_name = _text_from(variant, ("displayName", "name", "productName", "title", "label"))
        merged["displayName"] = variant_name if variant_name and not _looks_like_size(variant_name) else base_name
        variant_image_url = _image_url_from_node(variant)
        if variant_image_url:
            merged["_tc_image_url"] = variant_image_url
            merged["_tc_image_match_status"] = "EXACT_SKU_IMAGE"
            merged["_tc_image_source_scope"] = "variant"
        elif len(variants) == 1 and parent_image_url:
            merged["_tc_image_url"] = parent_image_url
            merged["_tc_image_match_status"] = "COMPATIBLE_SKU_IMAGE"
            merged["_tc_image_source_scope"] = "single_variant_parent"
        else:
            merged["_tc_image_url"] = ""
            merged["_tc_image_match_status"] = "NO_IMAGE"
            merged["_tc_image_source_scope"] = "variant_missing"
        expanded.append(merged)
    return expanded or [item]

# ==========================================================================
# CERTIFIED STATUS: BLOCKED_BY_PROVIDER
# Live Fire Evidence Date: 2026-08-26
# Test: curl_cffi chrome110 TLS impersonation -> HTTP 202 (WAF challenge)
# Test: Standard httpx HTTP/2                 -> HTTP 202 (WAF challenge)
# Conclusion: AWS WAF evaluates JavaScript execution, not TLS fingerprint alone.
# Resolution Path: WebView session cookie injection (Appium) or JS-render proxy.
# This connector parses payloads correctly when supplied from a solved session.
# ==========================================================================

class SwiggyInstamartConnector(BaseProviderConnector):
    PROVIDER_STATUS = "BLOCKED_BY_PROVIDER"
    BLOCK_EVIDENCE = "HTTP 202 AWS WAF JS challenge. Live-tested 2026-08-26."

    @property
    def provider_name(self) -> str:
        return "Swiggy Instamart"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            # Format A: flat products array from mobile WebView DOM fallback.
            flat_products = raw_payload.get("products", [])
            if flat_products and isinstance(flat_products[0], dict) and "sp" in flat_products[0]:
                seen = set()
                for item in flat_products[:25]:
                    price = float(item.get("sp", 0) or 0)
                    mrp = float(item.get("mrp", price) or price)
                    if not price:
                        continue
                    name = item.get("name", "Swiggy Instamart Product")
                    nav_id = str(item.get("skuId") or item.get("id") or item.get("url") or name)
                    unit = item.get("unit") or item.get("quantity") or item.get("quantityDescription") or "1 unit"
                    dedupe_key = f"{name}|{unit}|{price}".casefold()
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    product_url = item.get("url") or item.get("productUrl") or _swiggy_instamart_link(nav_id, name)
                    provider_price = ProviderPrice(
                        provider=self.provider_name,
                        price=price,
                        original_price=mrp if mrp > price else None,
                        delivery_time=item.get("delivery_time", ""),
                        deep_link=product_url,
                        product_url=product_url if str(product_url).startswith("http") else None,
                        fallback_search_url=_swiggy_instamart_search(name),
                        handoff_confidence="exact_product" if item.get("skuId") or item.get("id") else "search",
                        in_stock=item.get("in_stock") if isinstance(item.get("in_stock"), bool) else None,
                        serviceable=item.get("serviceable") if isinstance(item.get("serviceable"), bool) else None,
                    )
                    products.append(TrueCostProduct(
                        id=f"tc_swiggy_{abs(hash(dedupe_key))}",
                        name=name,
                        brand=item.get("brand") or item.get("brandName") or "Swiggy",
                        weight_volume=unit,
                        image_url=item.get("img_url", item.get("image_url", "")),
                        category="Grocery",
                        provider_sku=nav_id,
                        unknown_attributes={
                            "image_match_status": "EXACT_SKU_IMAGE" if item.get("img_url") or item.get("image_url") else "NO_IMAGE",
                            "image_source_provider": self.provider_name,
                            "image_source_product_id": nav_id,
                            "image_source_variant_id": nav_id,
                        },
                        prices=[provider_price]
                    ))
                return products

            def extract_items(node, results):
                if isinstance(node, dict):
                    has_variants = any(isinstance(node.get(key), list) for key in (
                        "variants",
                        "variations",
                        "variationList",
                        "variantList",
                        "skuVariants",
                        "productVariants",
                        "product_variants",
                        "options",
                        "productOptions",
                    ))
                    if "displayName" in node and (
                        ("price" in node and isinstance(node.get("price"), dict)) or has_variants
                    ):
                        results.append(node)
                    else:
                        for v in node.values():
                            extract_items(v, results)
                elif isinstance(node, list):
                    for item in node:
                        extract_items(item, results)

            items = []
            extract_items(raw_payload, items)

            expanded_items = []
            for item in items:
                expanded_items.extend(_expanded_items(item))

            seen = set()
            for item in expanded_items:
                offer_price, mrp = _price_from(item)
                if not offer_price:
                    continue
                skuid = item.get('skuId', item.get('sku_id', item.get('id', '')))
                name = item.get("displayName", item.get("name", "Unknown"))
                unit = item.get("quantityDescription", item.get("quantity", item.get("unit", item.get("weight", item.get("packSize", "1 unit")))))
                dedupe_key = f"{skuid}|{name}|{unit}|{offer_price}".casefold()
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                product_url = item.get("productUrl") or item.get("url") or _swiggy_instamart_link(skuid, name)
                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=float(offer_price),
                    original_price=float(mrp),
                    delivery_time=item.get("delivery_time", ""),
                    deep_link=product_url,
                    product_url=product_url if str(product_url).startswith("http") else None,
                    fallback_search_url=_swiggy_instamart_search(name),
                    handoff_confidence="exact_product" if skuid else "search",
                    in_stock=item.get("inStock", item.get("in_stock")) if isinstance(item.get("inStock", item.get("in_stock")), bool) else None,
                    serviceable=item.get("serviceable") if isinstance(item.get("serviceable"), bool) else None,
                )
                image_url = item.get("_tc_image_url", "")
                image_match_status = item.get("_tc_image_match_status") or ("EXACT_SKU_IMAGE" if image_url else "NO_IMAGE")
                tc_product = TrueCostProduct(
                    id=f"tc_swiggy_{skuid}",
                    name=name,
                    brand=item.get("brandName", item.get("brand", "Swiggy")),
                    weight_volume=unit,
                    image_url=image_url,
                    category="Grocery",
                    provider_sku=str(skuid or ""),
                    unknown_attributes={
                        "image_match_status": image_match_status,
                        "image_source_provider": self.provider_name if image_url else None,
                        "image_source_product_id": item.get("productId") or item.get("product_id") or skuid,
                        "image_source_variant_id": skuid,
                        "image_source_scope": item.get("_tc_image_source_scope"),
                    },
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[SwiggyConnector] Parsing Error: {e}")
        return products
