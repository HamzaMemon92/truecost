import pytest
from datetime import datetime, timedelta, timezone
from app.providers.grocery_base import GroceryProviderAdapter, GroceryProvider
from app.schemas.grocery import ProviderStatus, GrocerySourceType, Location

class DummyMockProvider(GroceryProvider):
    name = "DummyMock"
    status: ProviderStatus = "active"
    source_type: GrocerySourceType = "mock"
    timeout_ms = 4500
    
    async def search(self, query: str, location: Location | None = None) -> list[dict]:
        return []

class DummyLiveProvider(GroceryProvider):
    name = "DummyLive"
    status: ProviderStatus = "active"
    source_type: GrocerySourceType = "live"
    timeout_ms = 4500
    
    async def search(self, query: str, location: Location | None = None) -> list[dict]:
        return []

def test_mock_provider_defaults_to_fresh():
    adapter = GroceryProviderAdapter(DummyMockProvider())
    normalized = adapter.normalize([{"title": "Test", "price": 10.0}])
    
    item = normalized[0]
    assert item.freshness == "FRESH"
    assert item.price_checked_at is not None

def test_live_provider_missing_timestamp_is_unknown():
    adapter = GroceryProviderAdapter(DummyLiveProvider())
    normalized = adapter.normalize([{"title": "Test", "price": 10.0}])
    
    item = normalized[0]
    assert item.freshness == "UNKNOWN"

def test_live_provider_recent_timestamp_is_fresh():
    adapter = GroceryProviderAdapter(DummyLiveProvider())
    now = datetime.now(timezone.utc)
    recent = now - timedelta(minutes=5)
    
    normalized = adapter.normalize([{
        "title": "Test", 
        "price": 10.0,
        "retrieved_at": recent
    }])
    
    item = normalized[0]
    assert item.freshness == "FRESH"

def test_live_provider_old_timestamp_is_stale():
    adapter = GroceryProviderAdapter(DummyLiveProvider())
    now = datetime.now(timezone.utc)
    old = now - timedelta(hours=3)
    
    normalized = adapter.normalize([{
        "title": "Test", 
        "price": 10.0,
        "retrieved_at": old
    }])
    
    item = normalized[0]
    assert item.freshness == "STALE"

def test_independent_freshness_fields():
    adapter = GroceryProviderAdapter(DummyLiveProvider())
    now = datetime.now(timezone.utc)
    
    # We pass retrieved_at but we also test the independent fields map correctly
    normalized = adapter.normalize([{
        "title": "Test", 
        "price": 10.0,
        "retrieved_at": now - timedelta(minutes=5),
        "price_checked_at": now - timedelta(minutes=10),
        "availability_checked_at": now - timedelta(hours=3),
    }])
    
    item = normalized[0]
    assert item.freshness == "FRESH"
    assert item.price_checked_at == now - timedelta(minutes=10)
    assert item.availability_checked_at == now - timedelta(hours=3)
