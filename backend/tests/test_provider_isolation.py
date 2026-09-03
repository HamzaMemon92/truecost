import pytest
import asyncio
from typing import Any
from app.providers.grocery_base import GroceryProvider
from app.schemas.grocery import Location, ProviderStatus, GrocerySourceType, CanonicalGroceryItem
from app.providers.grocery_registry import execute_providers_concurrently

class SuccessProvider(GroceryProvider):
    name = "SuccessProvider"
    status: ProviderStatus = "active"
    source_type: GrocerySourceType = "mock"
    timeout_ms = 4500
    
    async def search(self, query: str, location: Location | None = None) -> list[CanonicalGroceryItem] | list[dict[str, Any]]:
        return [{"title": f"Success {query}", "price": 10.0}]

class TimeoutProvider(GroceryProvider):
    name = "TimeoutProvider"
    status: ProviderStatus = "active"
    source_type: GrocerySourceType = "mock"
    timeout_ms = 100 # Low timeout for test
    
    async def search(self, query: str, location: Location | None = None) -> list[CanonicalGroceryItem] | list[dict[str, Any]]:
        await asyncio.sleep(0.5)
        return [{"title": "Should Timeout", "price": 10.0}]

class ErrorProvider(GroceryProvider):
    name = "ErrorProvider"
    status: ProviderStatus = "active"
    source_type: GrocerySourceType = "mock"
    timeout_ms = 4500
    
    async def search(self, query: str, location: Location | None = None) -> list[CanonicalGroceryItem] | list[dict[str, Any]]:
        raise ValueError("Simulated provider failure")

@pytest.mark.asyncio
async def test_execute_providers_concurrently_isolation():
    providers = [SuccessProvider(), TimeoutProvider(), ErrorProvider()]
    
    all_products, observability = await execute_providers_concurrently(providers, ["milk"])
    
    # Assert successful products made it through
    assert len(all_products) == 1
    assert "Success milk" in all_products[0].title
    
    # Assert observability has 3 entries
    assert len(observability) == 3
    
    obs_success = next(o for o in observability if o["provider_name"] == "SuccessProvider")
    assert obs_success["status"] == "success"
    assert obs_success["item_count"] == 1
    
    obs_timeout = next(o for o in observability if o["provider_name"] == "TimeoutProvider")
    assert obs_timeout["status"] == "timeout"
    assert obs_timeout["error_class"] == "TimeoutError"
    
    obs_error = next(o for o in observability if o["provider_name"] == "ErrorProvider")
    assert obs_error["status"] == "error"
    assert obs_error["error_class"] == "ValueError"

@pytest.mark.asyncio
async def test_all_providers_fail():
    providers = [TimeoutProvider(), ErrorProvider()]
    
    all_products, observability = await execute_providers_concurrently(providers, ["milk"])
    
    # Assert empty products
    assert len(all_products) == 0
    
    # Assert observability records the failures
    assert len(observability) == 2
    assert all(o["status"] in ["timeout", "error"] for o in observability)
