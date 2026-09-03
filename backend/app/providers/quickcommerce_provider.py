from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.config import settings
from app.providers.grocery_base import GroceryProvider
from app.schemas.grocery import CanonicalGroceryItem, GrocerySourceType, ProviderStatus

logger = logging.getLogger(__name__)

# The platforms we fan-out across simultaneously.
_QC_PLATFORMS: list[dict[str, str]] = [
    {"slug": "BlinkIt",          "display": "Blinkit"},
    {"slug": "Zepto",            "display": "Zepto"},
    {"slug": "Swiggy Instamart", "display": "SwiggyInstamart"},
]

_QC_BASE_URL = "https://api.quickcommerceapi.com/v1"


def _parse_delivery_minutes(sla_str: str | None) -> int | None:
    """Parse '8 mins', '12 min', '15 minutes' → integer minutes."""
    if not sla_str:
        return None
    import re
    m = re.search(r"\d+", str(sla_str))
    return int(m.group()) if m else None


def _parse_quantity(qty_str: str | None) -> tuple[float, str]:
    """Parse '500 ml', '1 pack (6 pcs)', '2 x 200 ml' → (value, unit)."""
    if not qty_str:
        return 1.0, "unit"
    import re
    # Try simple number + unit: "500 ml", "1 kg", "12 pcs"
    m = re.match(r"^([\d.]+)\s*([a-zA-Z]+)", qty_str.strip())
    if m:
        try:
            return float(m.group(1)), m.group(2)
        except ValueError:
            pass
    # Try "1 pack (6 pcs)" → extract inner number
    m2 = re.search(r"\((\d+)\s*([a-zA-Z]+)\)", qty_str)
    if m2:
        try:
            return float(m2.group(1)), m2.group(2)
        except ValueError:
            pass
    return 1.0, "unit"


def _map_to_canonical(
    raw: dict[str, Any],
    platform_display: str,
    lat: float,
    lon: float,
) -> CanonicalGroceryItem | None:
    """Map a single QuickCommerce search result to our canonical schema.
    
    Real API response shape (confirmed):
    {
      "id": "542051",
      "name": "A2 Cow Milk",
      "brand": "Akshayakalpa Organic",
      "available": true,
      "images": ["https://cdn.grofers.com/...jpg"],
      "mrp": 47,
      "offer_price": 47,
      "quantity": "500 ml",
      "deeplink": "https://blinkit.com/prn/...",
      "rating": 4.55,
      "rating_count": 6950,
      "inventory": 4,
      "platform": {"name": "BlinkIt", "sla": "10 mins", "open": true, ...}
    }
    """
    try:
        name: str = raw.get("name") or raw.get("product_name") or ""
        if not name:
            return None

        offer_price = float(raw.get("offer_price") or raw.get("price") or 0.0)
        product_id: str = str(raw.get("id") or abs(hash(name + platform_display)))
        brand: str = raw.get("brand") or "Unknown"

        # Images — real CDN URLs from the API
        images: list[str] = raw.get("images") or []
        image_url = images[0] if images else ""
        deeplink: str = raw.get("deeplink") or raw.get("url") or ""

        # Availability — field is "available" (bool)
        availability_raw = raw.get("available")
        if availability_raw is True:
            availability = "In Stock"
        elif availability_raw is False:
            availability = "Out of Stock"
        else:
            # Fallback: check inventory count
            inventory = raw.get("inventory")
            if inventory is not None:
                availability = "In Stock" if int(inventory) > 0 else "Out of Stock"
            else:
                availability = "Unknown"

        # SLA is nested under platform.sla
        platform_meta: dict = raw.get("platform") or {}
        sla_str: str | None = platform_meta.get("sla") or raw.get("platform_sla") or raw.get("eta")
        delivery_minutes = _parse_delivery_minutes(sla_str)

        # Quantity parsing
        qty_value, qty_unit = _parse_quantity(raw.get("quantity"))

        now = datetime.now(timezone.utc)
        canonical_id = f"qcapi-{platform_display.lower()}-{product_id}"

        return CanonicalGroceryItem(
            canonical_product_id=canonical_id,
            provider=platform_display,
            provider_sku=product_id,
            title=name,
            brand=brand,
            category=raw.get("category") or "Grocery",
            quantity_value=qty_value,
            quantity_unit=qty_unit,
            price=offer_price,
            currency="INR",
            availability=availability,
            delivery_minutes=delivery_minutes,
            min_order_value=float(raw.get("min_order_value") or 0.0),
            offers=[raw.get("discount_label")] if raw.get("discount_label") else [],
            source_url=deeplink or image_url,
            affiliate_url=deeplink,
            source_type="live",
            provider_status="active",
            retrieved_at=now,
            expires_at=now + timedelta(minutes=10),
            confidence=0.95,
            image_verified=False,
            image_source="provider",
            retailer_image_url=image_url
        )
    except Exception as exc:
        logger.warning("QuickCommerce: failed to map item from %s: %s | raw=%s", platform_display, exc, raw.get("name", "?"))
        return None



class QuickCommerceProvider(GroceryProvider):
    """Integrates with the QuickCommerceAPI multiplexer.
    
    This provider calls one API that internally multiplexes across Zepto, Blinkit, and Swiggy.
    Since the data comes from a unified aggregator endpoint, we unpack it back into 
    separate canonical provider instances so the orchestration engine treats them equally.
    """
    
    name: str = "QuickCommerce API"
    status: ProviderStatus = "active"
    source_type: GrocerySourceType = "live"
    timeout_ms: int = 12000

    def is_enabled(self) -> bool:
        return bool(settings.quickcommerce_api_key)

    async def search(self, query: str, location: Location | None = None) -> list[CanonicalGroceryItem]:
        if not self.is_enabled():
            logger.debug("QuickCommerce: API key not configured, skipping.")
            return []

        platforms_env = getattr(settings, "quickcommerce_grocery_platforms", "BlinkIt,Zepto,Swiggy")
        
        lat = location.latitude if location and location.latitude else settings.quickcommerce_lat
        lon = location.longitude if location and location.longitude else settings.quickcommerce_lon
        
        params = {
            "q": query,
            "platforms": platforms_env,
        }
        
        if lat and lon:
            params["lat"] = str(lat)
            params["lon"] = str(lon)
        elif location and location.postal_code:
            params["pincode"] = location.postal_code
        else:
            # Fallback if no location info exists
            params["pincode"] = "560001"

        headers = {
            "X-API-Key": settings.quickcommerce_api_key,
            "Accept": "application/json",
            "User-Agent": "decision-advisor/1.0",
        }

        all_items: list[CanonicalGroceryItem] = []
        
        try:
            async with httpx.AsyncClient(headers=headers) as client:
                resp = await client.get(
                    f"{_QC_BASE_URL}/groupsearch",
                    params=params,
                    timeout=self.timeout_ms / 1000.0,
                )
                resp.raise_for_status()
                data = resp.json()

                credits_used = data.get("credit_cost")
                if credits_used:
                    logger.info("QuickCommerce API credits used: %s", credits_used)

                results_map = data.get("data", {}).get("results", {})
                
                for platform_name, products in results_map.items():
                    if not isinstance(products, list):
                        continue
                        
                    for raw in products[:10]:  # Cap at 10 per platform to prevent massive bloat
                        item = _map_to_canonical(
                            raw,
                            platform_name,
                            float(lat) if lat else 0.0,
                            float(lon) if lon else 0.0,
                        )
                        if item:
                            all_items.append(item)

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                logger.warning("QuickCommerce: rate limited on groupsearch")
            elif exc.response.status_code == 402:
                logger.warning("QuickCommerce: credits exhausted")
            else:
                logger.warning("QuickCommerce: HTTP %d", exc.response.status_code)
        except httpx.TimeoutException:
            logger.warning("QuickCommerce: timeout on groupsearch")
        except Exception as exc:
            logger.warning("QuickCommerce: unexpected error: %s", exc)

        logger.info(
            "QuickCommerce: total %d items across platforms for query '%s'",
            len(all_items),
            query,
        )
        return all_items
