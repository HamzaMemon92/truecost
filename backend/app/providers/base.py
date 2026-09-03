from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from app.schemas.shopping import CanonicalProduct


class ShoppingProvider(Protocol):
    name: str
    status: str

    def is_enabled(self) -> bool: ...

    async def search(self, query: str) -> list[CanonicalProduct] | list[dict[str, Any]]: ...


class ProviderAdapter:
    """Normalize provider payloads into the canonical shopping schema."""

    def __init__(self, provider: ShoppingProvider):
        self.provider = provider

    def normalize(self, payload: list[CanonicalProduct] | list[dict[str, Any]]) -> list[CanonicalProduct]:
        outputs: list[CanonicalProduct] = []
        for item in payload:
            if isinstance(item, CanonicalProduct):
                outputs.append(item)
                continue

            if not isinstance(item, dict):
                raise TypeError(f"Provider {self.provider.name} returned an invalid payload item: {type(item)!r}")

            normalized = self._coerce_to_canonical(item)
            outputs.append(normalized)

        return outputs

    def _coerce_to_canonical(self, item: dict[str, Any]) -> CanonicalProduct:
        now = datetime.now(timezone.utc)
        return CanonicalProduct(
            canonical_product_id=item.get("canonical_product_id") or f"{self.provider.name.lower()}-{item.get('title', 'unknown').lower().replace(' ', '-')}" ,
            provider=item.get("provider") or self.provider.name,
            provider_product_id=item.get("provider_product_id") or f"{self.provider.name.lower()}-{abs(hash(str(item.get('title', 'unknown')))) % 100000}",
            title=item["title"],
            brand=item.get("brand") or "Unknown",
            category=item.get("category") or "General",
            variant=item.get("variant") or "standard",
            price=float(item.get("price", 0.0)),
            currency=item.get("currency") or "INR",
            availability=item.get("availability") or "Unknown",
            seller=item.get("seller") or self.provider.name,
            rating=float(item.get("rating", 0.0)),
            review_count=int(item.get("review_count", 0)),
            delivery=item.get("delivery") or "Unknown",
            offers=item.get("offers") or [],
            return_policy=item.get("return_policy") or "Not specified",
            warranty=item.get("warranty") or "Not specified",
            source_url=item.get("source_url") or "https://example.com",
            affiliate_url=item.get("affiliate_url") or item.get("source_url") or "https://example.com",
            source_type=item.get("source_type") or self.provider.status,
            retrieved_at=item.get("retrieved_at") or now,
            expires_at=item.get("expires_at") or (now + timedelta(minutes=30)),
            confidence=float(item.get("confidence", 0.9)),
        )


def normalize_provider_results(provider: ShoppingProvider, payload: list[CanonicalProduct] | list[dict[str, Any]]) -> list[CanonicalProduct]:
    return ProviderAdapter(provider).normalize(payload)
