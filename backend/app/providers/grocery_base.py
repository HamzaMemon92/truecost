from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from app.schemas.grocery import CanonicalGroceryItem, ProviderStatus, GrocerySourceType, Location


class GroceryProvider(Protocol):
    name: str
    status: ProviderStatus
    source_type: GrocerySourceType
    timeout_ms: int

    async def search(self, query: str, location: Location | None = None) -> list[CanonicalGroceryItem] | list[dict[str, Any]]: ...


class GroceryProviderAdapter:
    """Normalize provider payloads into the canonical grocery schema."""

    def __init__(self, provider: GroceryProvider):
        self.provider = provider

    def normalize(self, payload: list[CanonicalGroceryItem] | list[dict[str, Any]]) -> list[CanonicalGroceryItem]:
        outputs: list[CanonicalGroceryItem] = []
        for item in payload:
            if isinstance(item, CanonicalGroceryItem):
                outputs.append(item)
                continue

            if not isinstance(item, dict):
                raise TypeError(f"Provider {self.provider.name} returned an invalid payload item: {type(item)!r}")

            normalized = self._coerce_to_canonical(item)
            outputs.append(normalized)

        return outputs

    def _coerce_to_canonical(self, item: dict[str, Any]) -> CanonicalGroceryItem:
        now = datetime.now(timezone.utc)
        
        source_type = getattr(self.provider, "source_type", "mock")
        image_confidence = item.get("image_confidence", "UNVERIFIED")
        
        # Never implicitly TRUST live retailer images until verified by admin/system
        if source_type == "live" and image_confidence == "TRUSTED":
            image_confidence = "KNOWN_SOURCE"
            
        raw_retrieved_at = item.get("retrieved_at")
        
        # Determine actual timestamp based on mock vs live
        effective_ts = raw_retrieved_at
        if not effective_ts and source_type == "mock":
            effective_ts = now
            
        price_checked_at = item.get("price_checked_at") or effective_ts
        availability_checked_at = item.get("availability_checked_at") or effective_ts
        image_checked_at = item.get("image_checked_at") or effective_ts
        
        def _eval_fresh(ts: datetime | None) -> str:
            if not ts:
                return "FRESH" if source_type == "mock" else "UNKNOWN"
            age = now - ts
            return "FRESH" if age.total_seconds() < 7200 else "STALE"

        freshness = _eval_fresh(raw_retrieved_at)
                
        return CanonicalGroceryItem(
            canonical_product_id=item.get("canonical_product_id") or f"{self.provider.name.lower()}-{item.get('title', 'unknown').lower().replace(' ', '-')}",
            provider=item.get("provider") or self.provider.name,
            provider_sku=item.get("provider_sku") or f"{self.provider.name.lower()}-{abs(hash(str(item.get('title', 'unknown')))) % 100000}",
            title=item["title"],
            brand=item.get("brand") or "Unknown",
            category=item.get("category") or "Grocery",
            quantity_value=float(item.get("quantity_value", 1.0)),
            quantity_unit=item.get("quantity_unit") or "unit",
            price=float(item.get("price", 0.0)),
            mrp=float(item.get("mrp")) if item.get("mrp") is not None else None,
            discount=float(item.get("discount", 0.0)),
            coupon_discount=float(item.get("coupon_discount", 0.0)),
            delivery_fee=float(item.get("delivery_fee", 0.0)),
            platform_fee=float(item.get("platform_fee", 0.0)),
            currency=item.get("currency") or "INR",
            availability=item.get("availability") or "Unknown",
            delivery_minutes=int(item.get("delivery_minutes", 30)) if item.get("delivery_minutes") is not None else None,
            min_order_value=float(item.get("min_order_value", 0.0)) if item.get("min_order_value") is not None else None,
            offers=item.get("offers") or [],
            source_url=item.get("source_url") or "https://example.com",
            affiliate_url=item.get("affiliate_url") or item.get("source_url") or "https://example.com",
            source_type=source_type,
            provider_status=self.provider.status,
            retrieved_at=effective_ts or now,
            expires_at=item.get("expires_at") or (now + timedelta(minutes=30)),
            confidence=float(item.get("confidence", 0.9)),
            freshness=freshness,
            price_checked_at=price_checked_at,
            availability_checked_at=availability_checked_at,
            image_checked_at=image_checked_at,
            image_confidence=image_confidence
        )


def normalize_grocery_results(provider: GroceryProvider, payload: list[CanonicalGroceryItem] | list[dict[str, Any]]) -> list[CanonicalGroceryItem]:
    return GroceryProviderAdapter(provider).normalize(payload)
