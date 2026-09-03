import re
from urllib.parse import quote_plus
from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice

def _slug(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").casefold()).strip("-")
    return text or "product"

def _blinkit_link(product_id: Any, name: Any) -> str:
    pid = str(product_id or "").strip()
    if pid and pid.isdigit():
        return f"https://blinkit.com/prn/{_slug(name)}/prid/{pid}"
    return f"https://blinkit.com/s/?q={quote_plus(str(name or '').strip())}"

def _blinkit_search(name: Any) -> str:
    return f"https://blinkit.com/s/?q={quote_plus(str(name or '').strip())}"

def _as_price(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, dict):
        for key in ("price", "sp", "selling_price", "sellingPrice", "final_price", "finalPrice", "amount", "units", "value"):
            parsed = _as_price(value.get(key))
            if parsed:
                return parsed
        return None
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(value or ""))
        if not match:
            return None
        number = float(match.group(1))
    return number / 100 if number > 999 else number

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

def _first_image(item: Dict[str, Any], *, nested_media: bool = False) -> str:
    keys = ("img_url", "image_url", "imageUrl", "image", "thumbnail", "thumbnail_url", "url", "path") if nested_media else ("img_url", "image_url", "imageUrl", "image", "thumbnail", "thumbnail_url")
    direct = _first_text(item, keys)
    if direct:
        return direct
    for key in ("images", "imageUrls", "media", "assets"):
        value = item.get(key)
        if isinstance(value, list):
            for entry in value:
                if isinstance(entry, str) and entry.strip():
                    return entry.strip()
                if isinstance(entry, dict):
                    nested = _first_image(entry, nested_media=True)
                    if nested:
                        return nested
        elif isinstance(value, dict):
            nested = _first_image(value, nested_media=True)
            if nested:
                return nested
    return ""

def _availability(item: Dict[str, Any]) -> bool | None:
    for key in ("in_stock", "inStock", "available", "isAvailable", "serviceable"):
        value = item.get(key)
        if isinstance(value, bool):
            return value
    for key in ("inventory", "availability", "stock"):
        value = item.get(key)
        if isinstance(value, dict):
            nested = _availability(value)
            if nested is not None:
                return nested
        elif isinstance(value, str):
            return not bool(re.search(r"out|sold|unavailable", value, flags=re.I))
        elif isinstance(value, (int, float)):
            return value > 0
    return None

def _generic_product(item: Dict[str, Any]) -> dict[str, Any] | None:
    name = _first_text(item, ("product_name", "productName", "display_name", "displayName", "name", "title", "item_name", "itemName"))
    pricing = item.get("pricing") if isinstance(item.get("pricing"), dict) else {}
    price = (
        _as_price(item.get("sp"))
        or _as_price(item.get("price"))
        or _as_price(item.get("selling_price"))
        or _as_price(item.get("sellingPrice"))
        or _as_price(item.get("final_price"))
        or _as_price(item.get("finalPrice"))
        or _as_price(item.get("offer_price"))
        or _as_price(item.get("offerPrice"))
        or _as_price(pricing.get("selling_price"))
        or _as_price(pricing.get("sellingPrice"))
        or _as_price(pricing.get("final_price"))
        or _as_price(pricing.get("finalPrice"))
        or _as_price(pricing.get("offer_price"))
        or _as_price(pricing.get("offerPrice"))
        or _as_price(pricing.get("price"))
    )
    if not name or not price:
        return None
    unit = _first_text(item, ("unit", "weight", "weightVolume", "weight_volume", "pack_size", "packSize", "formattedPacksize", "quantity", "quantityDescription", "variant")) or "1 unit"
    pid = _first_text(item, ("product_id", "productId", "id", "sku_id", "skuId", "variant_id", "variantId", "nav_id")) or name
    return {
        "name": name,
        "brand": _first_text(item, ("brand", "brandName", "manufacturer")) or ("Amul" if "amul" in name.casefold() else "Blinkit"),
        "sp": price,
        "mrp": _as_price(item.get("mrp")) or _as_price(item.get("original_price")) or _as_price(pricing.get("mrp")) or price,
        "unit": unit,
        "img_url": _first_image(item),
        "nav_id": str(pid),
        "url": _first_text(item, ("url", "product_url", "productUrl", "deeplink", "deep_link")),
        "in_stock": _availability(item),
    }

def _collect_generic_products(raw_payload: Dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen_nodes: set[int] = set()

    def walk(node: Any) -> None:
        if len(found) >= 80 or node is None:
            return
        if isinstance(node, dict):
            node_id = id(node)
            if node_id in seen_nodes:
                return
            seen_nodes.add(node_id)
            product = _generic_product(node)
            if product:
                found.append(product)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(raw_payload)
    deduped: dict[str, dict[str, Any]] = {}
    for item in found:
        key = f"{item.get('nav_id')}|{item.get('name')}|{item.get('unit')}|{item.get('sp')}".casefold()
        deduped.setdefault(key, item)
    return list(deduped.values())

class BlinkitConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Blinkit"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            # Format A: flat products array from scraper {name, sp, mrp, brand, unit, img_url, nav_id}
            flat_products = raw_payload.get("products", [])
            if flat_products and isinstance(flat_products[0], dict) and "sp" in flat_products[0]:
                seen = set()
                for item in flat_products[:25]:
                    price = float(item.get("sp", 0) or 0)
                    mrp = float(item.get("mrp", price) or price)
                    if not price:
                        continue
                    name = item.get("name", "Blinkit Product")
                    nav_id = str(item.get("nav_id", item.get("id", hash(name) % 999999)))
                    if nav_id in seen:
                        continue
                    seen.add(nav_id)
                    product_url = item.get("url") or _blinkit_link(nav_id, name)
                    provider_price = ProviderPrice(
                        provider=self.provider_name,
                        price=price,
                        original_price=mrp if mrp > price else None,
                        delivery_time=item.get("delivery_time", ""),
                        deep_link=product_url,
                        product_url=product_url if str(product_url).startswith("http") else None,
                        fallback_search_url=_blinkit_search(name),
                        handoff_confidence="exact_product" if nav_id.isdigit() else "search",
                        in_stock=item.get("in_stock") if isinstance(item.get("in_stock"), bool) else None,
                        serviceable=item.get("serviceable") if isinstance(item.get("serviceable"), bool) else None,
                    )
                    products.append(TrueCostProduct(
                        id=f"tc_blinkit_{nav_id}",
                        name=name,
                        brand=item.get("brand", "Blinkit"),
                        weight_volume=item.get("unit", "1 unit"),
                        image_url=item.get("img_url", item.get("image_url", "")),
                        category="Grocery",
                        provider_sku=nav_id,
                        unknown_attributes={
                            "image_match_status": "EXACT_SKU_IMAGE" if item.get("img_url") or item.get("image_url") else "NO_IMAGE",
                            "image_source_provider": self.provider_name if item.get("img_url") or item.get("image_url") else None,
                            "image_source_product_id": nav_id,
                            "image_source_variant_id": nav_id,
                        },
                        prices=[provider_price]
                    ))
                return products

            # Format B: nested cart_item shape from Blinkit GraphQL API
            items = []
            def find_cart_items(node):
                if isinstance(node, dict):
                    if "cart_item" in node and "product_name" in node["cart_item"]:
                        items.append(node["cart_item"])
                    for k, v in node.items():
                        find_cart_items(v)
                elif isinstance(node, list):
                    for item in node:
                        find_cart_items(item)

            find_cart_items(raw_payload)

            if not items:
                items = _collect_generic_products(raw_payload)

            seen_ids = set()
            for item in items:
                pid = item.get("product_id") or item.get("id") or item.get("nav_id")
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                price = item.get("price") or item.get("sp")
                mrp = item.get("mrp", price)
                if not price:
                    continue
                name = item.get("display_name", item.get("product_name", item.get("name", "Unknown")))
                product_url = _blinkit_link(pid, name)
                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=float(price),
                    original_price=float(mrp),
                    delivery_time=item.get("delivery_time", ""),
                    deep_link=product_url,
                    product_url=product_url,
                    fallback_search_url=_blinkit_search(name),
                    handoff_confidence="exact_product" if str(pid or "").isdigit() else "search",
                    in_stock=item.get("in_stock") if isinstance(item.get("in_stock"), bool) else None,
                    serviceable=item.get("serviceable") if isinstance(item.get("serviceable"), bool) else None,
                )
                products.append(TrueCostProduct(
                    id=f"tc_blinkit_{pid}",
                    name=name,
                    brand=item.get("brand", "Blinkit"),
                    weight_volume=item.get("unit", "1 unit"),
                    image_url=item.get("image_url", item.get("img_url", "")),
                    category="Grocery",
                    provider_sku=str(pid or ""),
                    unknown_attributes={
                        "image_match_status": "EXACT_SKU_IMAGE" if item.get("image_url") or item.get("img_url") else "NO_IMAGE",
                        "image_source_provider": self.provider_name if item.get("image_url") or item.get("img_url") else None,
                        "image_source_product_id": pid,
                        "image_source_variant_id": pid,
                    },
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[BlinkitConnector] Parsing Error: {e}")
        return products
