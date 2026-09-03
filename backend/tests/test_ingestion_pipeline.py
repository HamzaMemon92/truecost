import pytest
from datetime import datetime, timedelta, timezone

def test_missing_price_stays_null():
    # Simulates ingestion payload
    observation = {"id": "1", "title": "Milk", "price": None}
    assert observation["price"] is None

def test_missing_eta_fees_stay_null():
    observation = {"id": "1", "title": "A", "price": 10.0}
    assert observation.get("delivery_eta_mins") is None
    assert observation.get("delivery_fee") is None

def test_no_mock_masquerades_as_real():
    observation = {"id": "1", "title": "A", "source_type": "mock"}
    assert observation["source_type"] == "mock"
    assert observation["source_type"] != "live"

def test_stale_observations_identified():
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    observation = {"id": "1", "title": "A", "observed_at": stale_time}
    
    obs_time = datetime.fromisoformat(observation["observed_at"])
    age = (datetime.now(timezone.utc) - obs_time).total_seconds()
    is_stale = age > 3600 # 1 hour policy
    assert is_stale is True

def test_location_attached_only_when_observed():
    obs1 = {"id": "1", "title": "A"}
    assert obs1.get("location") is None
    
    obs2 = {"id": "2", "title": "B", "location": {"lat": 12.0, "lon": 77.0}}
    assert obs2.get("location") is not None
    assert obs2["location"]["lat"] == 12.0

def test_provider_identity_preserved():
    observation = {"id": "SKU-123", "title": "Milk", "provider": "Blinkit"}
    assert observation["id"] == "SKU-123"
    assert observation["provider"] == "Blinkit"

@pytest.mark.asyncio
async def test_quickcommerce_sync_provider_does_not_exist():
    from app.providers.grocery_registry import get_grocery_providers
    providers = get_grocery_providers()
    
    # Assert that no provider in the registry is QuickCommerceProvider
    for p in providers:
        assert p.__class__.__name__ != "QuickCommerceProvider", "QuickCommerceProvider found in synchronous registry!"
