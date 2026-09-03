"""
Grocery Observation Repository

Boundary: reads and writes TrueCostProduct dicts as stored by aggregator/ingest.

Production durability: CACHE_ONLY
  - MemoryPriceCache in test/development environments
  - RedisPriceCache in production
  - Redis key pattern: price:grocery:{provider}:{sha256(query)[:24]}
  - Redis TTL: 900 seconds (default)

Duplicate semantics: last-write-wins per (query, provider).
A later ingestion for the same query+provider replaces the previous observation.

Schema bridge:
  Ingestion writes TrueCostProduct dicts (camelCase: id, name, brand, prices[{provider,price,...}])
  MCP/workflow expects CanonicalGroceryItem dicts (snake_case: canonical_product_id, title, price,...)
  _tc_product_to_canonical_dict() bridges these schemas.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.services.cache import cache


# Certified grocery providers for ingestion-based observations
GROCERY_OBSERVATION_PROVIDERS = [
    "blinkit",
    "zepto",
    "swiggy",
    "bigbasket",
]


def _tc_product_to_canonical_dict(product: dict[str, Any], query: str) -> dict[str, Any] | None:
    """
    Convert a TrueCostProduct dict (camelCase, from aggregator/ingest) into a
    CanonicalGroceryItem-compatible dict for the Grocery MCP / workflow.

    TrueCostProduct fields (camelCase from connector normalization):
        id, name, brand, weightVolume, imageUrl, category,
        prices: [{provider, price, originalPrice, deliveryTime, deepLink}]

    CanonicalGroceryItem fields (snake_case for grocery workflow):
        canonical_product_id, provider, provider_sku, title, brand,
        category, quantity_value, quantity_unit, price, mrp,
        availability, source_url, affiliate_url, source_type

    Returns None if the product cannot be safely converted (missing price).
    """
    prices = product.get("prices") or []
    if not prices:
        return None

    offer = prices[0]
    price_val = offer.get("price")
    if price_val is None:
        return None

    provider = str(offer.get("provider") or "").strip().lower()
    deep_link = str(offer.get("deepLink") or offer.get("deep_link") or "")
    weight = str(product.get("weightVolume") or product.get("weight_volume") or "")

    # In shadow ER mode, the entity resolution does not overwrite product.id
    # We must use the ER decision to map to canonical_catalog, if it was an EXACT match
    er = product.get("entityResolution") or {}
    er_decision = er.get("decision")
    
    if er_decision == "EXACT" and er.get("identity_fingerprint"):
        product_id = str(er.get("identity_fingerprint"))
    else:
        product_id = str(product.get("id") or "")

    mrp_val = offer.get("originalPrice") or offer.get("original_price") or price_val
    in_stock = offer.get("inStock")
    if in_stock is None:
        in_stock = offer.get("in_stock")

    # Parse quantity from weight string (e.g. "500ml", "1kg", "1 unit", "250 g")
    qty_match = re.match(r"^([\d.]+)\s*(.*)$", weight.strip())
    quantity_value = float(qty_match.group(1)) if qty_match else 1.0
    quantity_unit = qty_match.group(2).strip() if qty_match else "unit"
    if not quantity_unit:
        quantity_unit = "unit"

    # Carry ER audit fields if ingest decorated them
    er = product.get("entityResolution") or {}

    return {
        "canonical_product_id": product_id,
        "provider": provider or "unknown",
        "provider_sku": product_id,
        "title": str(product.get("name") or ""),
        "brand": str(product.get("brand") or ""),
        "category": str(product.get("category") or "Grocery"),
        "quantity_value": quantity_value,
        "quantity_unit": quantity_unit,
        "price": float(price_val),
        "mrp": float(mrp_val),
        "discount": 0.0,
        "currency": "INR",
        "availability": "IN_STOCK" if in_stock is True else "OUT_OF_STOCK" if in_stock is False else "UNKNOWN",
        "delivery_minutes": None,
        "source_url": deep_link or "",
        "affiliate_url": deep_link or "",
        "source_type": "live",
        "provider_status": "active",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + __import__("datetime").timedelta(minutes=30)).isoformat(),
        "confidence": 0.9,
        # Provenance / traceability
        "er_decision": er.get("decision"),
        "er_confidence": er.get("confidence"),
        "er_resolver_version": er.get("resolver_version"),
        "ingestion_freshness": "live",
        "ingested_query": query,
    }


class GroceryObservationRepository:
    """Read/write boundary for grocery provider observations.

    Durability model: CACHE_ONLY
      - MemoryPriceCache in test/development (no persistence across restarts)
      - RedisPriceCache in production (TTL=900s, key=price:grocery:{provider}:{digest})

    All reads go through this boundary. The Grocery MCP MUST NOT call
    get_grocery_providers() or execute_providers_concurrently() for user queries.
    """

    def __init__(self) -> None:
        self._cache = cache

    def write_observations(self, query: str, provider: str, data: list[Any], *, location: dict[str, Any] | None = None) -> None:
        """Write normalized TrueCostProduct dicts for a query+provider.
        Semantics: last-write-wins. A later ingestion replaces the previous entry.
        """
        self._cache.set(query, provider, "Grocery", data, location=location)

    def search_observations(
        self, query: str, providers: list[str] | None = None, *, location: dict[str, Any] | None = None
    ) -> dict[str, list[Any]]:
        """Return raw TrueCostProduct dicts keyed by provider.
        Only includes providers that have observations (no None values).
        """
        resolved = providers or GROCERY_OBSERVATION_PROVIDERS
        res = self._cache.get_all_providers(query, "Grocery", resolved, location=location)
        return {k: v for k, v in res.items() if v is not None}

    def get_provider_offers(self, query: str, provider: str, *, location: dict[str, Any] | None = None) -> list[Any]:
        """Return raw TrueCostProduct dicts for one provider, or [] if none."""
        return self._cache.get(query, provider, "Grocery", location=location) or []

    def search_observations_as_canonical(
        self, query: str, providers: list[str] | None = None, *, location: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Return CanonicalGroceryItem-compatible dicts for Grocery MCP / workflow.

        Converts TrueCostProduct dicts (from ingest storage) into the schema
        that the Grocery workflow's _basket_pipeline expects.

        Returns empty list when no observations exist.
        NEVER falls back to live provider network calls.
        """
        raw_by_provider = self.search_observations(query, providers, location=location)
        canonical_items: list[dict[str, Any]] = []
        for raw_list in raw_by_provider.values():
            for product in (raw_list or []):
                canonical = _tc_product_to_canonical_dict(product, query)
                if canonical is not None:
                    canonical_items.append(canonical)
        return canonical_items

    def get_latest_by_provider_sku(
        self, query: str, provider: str, sku: str
    ) -> dict[str, Any] | None:
        """Find a specific SKU within a provider's cached observation."""
        for offer in self.get_provider_offers(query, provider):
            if offer.get("id") == sku:
                return offer
        return None

    def has_observations(self, query: str, providers: list[str] | None = None, *, location: dict[str, Any] | None = None) -> bool:
        """Returns True if any observations exist for this query."""
        return bool(self.search_observations(query, providers, location=location))


grocery_observations = GroceryObservationRepository()
