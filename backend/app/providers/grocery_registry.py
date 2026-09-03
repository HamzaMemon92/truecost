from __future__ import annotations

import asyncio
import time
from typing import Any

from app.providers.grocery_base import GroceryProvider
from app.providers.mock_grocery_provider import MockCheapGroceryProvider, MockFastGroceryProvider, MockGoldenGroceryProvider
from app.providers.quickcommerce_provider import QuickCommerceProvider
from app.providers.mock_ondc_provider import MockOndcProvider
from app.schemas.grocery import Location, CanonicalGroceryItem


def get_grocery_providers() -> list[GroceryProvider]:
    """Return the list of configured grocery providers.
    
    Mock providers are always registered (for testing and fallback).
    Real providers are registered only if their API keys are present.
    """
    providers: list[GroceryProvider] = [
        MockGoldenGroceryProvider(),
        MockFastGroceryProvider(),
        MockCheapGroceryProvider(),
        MockOndcProvider(),
    ]

    # Register real providers behind feature flags
    from app.providers.flipkart_grocery_provider import FlipkartGroceryProvider
    fk = FlipkartGroceryProvider()
    if fk.is_enabled():
        providers.insert(0, fk)

    qc = QuickCommerceProvider()
    if qc.is_enabled():
        # Real provider goes first so it wins ranking ties
        providers.insert(0, qc)

    return providers


async def execute_providers_concurrently(
    providers: list[GroceryProvider],
    queries: list[str],
    location: Location | None = None
) -> tuple[list[CanonicalGroceryItem], list[dict[str, Any]]]:
    """Execute all providers safely, returning aggregated products and observability."""
    all_products: list[CanonicalGroceryItem] = []
    observability: list[dict[str, Any]] = []

    async def fetch_for_provider(provider: GroceryProvider) -> tuple[list[CanonicalGroceryItem], dict[str, Any]]:
        start_time = time.time()
        obs = {
            "provider_name": provider.name,
            "status": "error",
            "latency_ms": 0,
            "error_class": None,
            "item_count": 0
        }
        
        provider_items = []
        timeout_val = getattr(provider, "timeout_ms", 4500) / 1000.0
        
        try:
            for query in queries:
                products_raw = await asyncio.wait_for(provider.search(query, location=location), timeout=timeout_val)
                from app.providers.grocery_base import normalize_grocery_results
                normalized = normalize_grocery_results(provider, products_raw)
                provider_items.extend(normalized)
            
            obs["status"] = "success" if provider_items else "no_results"
            obs["item_count"] = len(provider_items)
            return provider_items, obs
            
        except asyncio.TimeoutError:
            obs["status"] = "timeout"
            obs["error_class"] = "TimeoutError"
        except Exception as e:
            print(f"Provider {provider.name} failed with {repr(e)}")
            obs["status"] = "error"
            obs["error_class"] = e.__class__.__name__
        finally:
            obs["latency_ms"] = int((time.time() - start_time) * 1000)
            
        return [], obs

    results = await asyncio.gather(*[fetch_for_provider(p) for p in providers], return_exceptions=True)
    
    for res in results:
        if isinstance(res, tuple):
            items, obs = res
            all_products.extend(items)
            observability.append(obs)
        elif isinstance(res, Exception):
            # This shouldn't happen due to our try/except, but just in case
            print(f"Provider failed unexpectedly: {repr(res)}")
            observability.append({
                "provider_name": "Unknown",
                "status": "error",
                "error_class": res.__class__.__name__,
                "item_count": 0
            })
            
    return all_products, observability
