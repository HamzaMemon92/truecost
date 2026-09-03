from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.config import settings
from app.providers.grocery_base import GroceryProvider
from app.schemas.grocery import CanonicalGroceryItem, GrocerySourceType, ProviderStatus, Location

logger = logging.getLogger(__name__)


def _parse_quantity(title: str, attrs: str | None) -> tuple[float, str]:
    """Extract weight/volume from title or attributes."""
    import re
    search_str = f"{title} {attrs or ''}".lower()
    
    # Match "500 ml", "1 kg", "200g"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(ml|l|kg|g|gm|oz|lb|pcs|pack)\b", search_str)
    if m:
        try:
            val = float(m.group(1))
            unit = m.group(2)
            if unit == "gm":
                unit = "g"
            return val, unit
        except ValueError:
            pass
            
    return 1.0, "unit"


class RateLimitError(Exception):
    pass

class FlipkartGroceryProvider(GroceryProvider):
    name: str = "Flipkart Grocery"
    timeout_ms: int = 4500

    @property
    def status(self) -> ProviderStatus:
        if settings.flipkart_affiliate_id and settings.flipkart_affiliate_token:
            return "active"
        return "pending_authorization"

    @property
    def source_type(self) -> GrocerySourceType:
        # This is a live provider. If it's disabled, it's just unavailable.
        return "live"

    def is_enabled(self) -> bool:
        return self.status == "active"

    async def search(self, query: str, location: Location | None = None) -> list[CanonicalGroceryItem]:
        if not self.is_enabled():
            logger.debug("Flipkart Grocery: credentials absent, skipping live call.")
            return []

        # 1. VERIFY THE ACTUAL OFFICIAL SEARCH ENDPOINT
        url = "https://affiliate-api.flipkart.net/affiliate/1.0/search.json"
        headers = {
            "Fk-Affiliate-Id": settings.flipkart_affiliate_id,
            "Fk-Affiliate-Token": settings.flipkart_affiliate_token,
            "Accept": "application/json",
            "User-Agent": "decision-advisor/1.0",
        }
        params = {"query": query, "resultCount": 10}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_ms / 1000.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                retry_after = exc.response.headers.get("Retry-After", "unknown")
                logger.warning(f"Flipkart Grocery: Rate limited. Retry-After: {retry_after}")
                raise RateLimitError(f"Rate limited (Retry-After: {retry_after})")
            else:
                logger.warning("Flipkart Grocery: HTTP %d", exc.response.status_code)
                raise
        except httpx.TimeoutException:
            logger.warning("Flipkart Grocery: Timeout reached.")
            raise
        except Exception as exc:
            logger.warning("Flipkart Grocery: Unexpected error: %s", exc)
            raise

        entries = payload.get("productInfoList", [])
        if not entries:
            return []

        products: list[CanonicalGroceryItem] = []
        now = datetime.now(timezone.utc)

        for entry in entries:
            # Isolate version-specific parsing
            if "productBaseInfoV1" in entry:
                base = entry["productBaseInfoV1"]
                
                title = str(base.get("title") or "").strip()
                if not title:
                    continue  # Reject malformed missing title

                selling_price = base.get("sellingPrice", {}).get("amount", 0) if isinstance(base.get("sellingPrice"), dict) else base.get("sellingPrice", 0)
                maximum_price = base.get("maximumRetailPrice", {}).get("amount", selling_price) if isinstance(base.get("maximumRetailPrice"), dict) else base.get("maximumRetailPrice", selling_price)
                
                selling_price = float(selling_price)
                maximum_price = float(maximum_price)
                if selling_price <= 0:
                    continue  # Reject invalid price

                brand = str(base.get("productBrand") or "Unknown")
                product_id = str(base.get("productId") or title)
                category = str(base.get("categoryPath") or "Grocery")

                in_stock_raw = str(base.get("inStock", "false")).lower()
                # Explicitly map to catalog availability, not instant-fulfillment
                availability = "In Stock" if in_stock_raw == "true" else "Out of Stock"
                
                offers = base.get("offers") or []
                product_url = str(base.get("productUrl") or "")
                image_url = str(base.get("imageUrls", {}).get("400x400") or "")

                qty_val, qty_unit = _parse_quantity(title, str(base.get("attributes")))
            else:
                # If newer versions (e.g. V2) are present, parse them here.
                # Currently skipping unknown structures.
                continue

            # Discount is MRP - selling price
            discount = max(0.0, maximum_price - selling_price)

            canonical_id = f"flipkart-groc-{title.lower().replace(' ', '-')}-{product_id}"

            item = CanonicalGroceryItem(
                canonical_product_id=canonical_id,
                provider=self.name,
                provider_sku=product_id,
                title=title,
                brand=brand,
                category=category,
                quantity_value=qty_val,
                quantity_unit=qty_unit,
                price=selling_price,
                mrp=maximum_price,
                discount=discount,
                coupon_discount=None,  # Do not fabricate 0.0
                delivery_fee=None,     # Do not fabricate 0.0
                platform_fee=None,     # Do not fabricate 0.0
                currency="INR",
                availability=availability,
                # Explicitly DO NOT map Flipkart catalog/shipping fields into quick-commerce instant ETA
                delivery_minutes=None,  
                min_order_value=None,  # Do not fabricate 0.0
                offers=[str(o) for o in offers],
                source_url=product_url,
                affiliate_url=product_url, # ProductURL natively contains affiliate tracking
                source_type="live",
                provider_status="active",
                retrieved_at=now,
                expires_at=now + timedelta(minutes=30),
                retailer_image_url=image_url if image_url else None,
                image_verified=False, # We have an image, but it is not strongly identity-verified
                image_source=self.name if image_url else None,
                deep_link_type="PRODUCT_PAGE" if product_url else "UNAVAILABLE",
                deep_link_url=product_url if product_url else None,
                freshness="UNKNOWN", # Leave it for the downstream policy
                price_checked_at=now,
                availability_checked_at=now,
                image_checked_at=now
            )
            products.append(item)

        return products
