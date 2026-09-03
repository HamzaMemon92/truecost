from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.providers.base import normalize_provider_results
from app.schemas.shopping import CanonicalProduct


class ExampleRealProvider:
    name = "ExampleProvider"
    status = "live"

    async def search(self, query: str):
        return [{
            "provider": "ExampleProvider",
            "provider_product_id": "EP-1001",
            "title": "Apple iPhone 15",
            "brand": "Apple",
            "category": "Mobile",
            "variant": "128GB",
            "price": 69999,
            "currency": "INR",
            "availability": "In stock",
            "seller": "Example Retail",
            "rating": 4.7,
            "review_count": 1800,
            "delivery": "2 days",
            "offers": ["Cashback", "EMI"],
            "return_policy": "7-day return",
            "warranty": "1 year",
            "source_url": "https://example.com/iphone15",
            "affiliate_url": "https://example.com/affiliate/iphone15",
            "source_type": "live",
            "retrieved_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
            "confidence": 0.92,
        }]


def test_single_real_provider_normalizes_into_canonical_schema():
    provider = ExampleRealProvider()
    payload = [{
        "provider": "ExampleProvider",
        "provider_product_id": "EP-1001",
        "title": "Apple iPhone 15",
        "brand": "Apple",
        "category": "Mobile",
        "variant": "128GB",
        "price": 69999,
        "currency": "INR",
        "availability": "In stock",
        "seller": "Example Retail",
        "rating": 4.7,
        "review_count": 1800,
        "delivery": "2 days",
        "offers": ["Cashback", "EMI"],
        "return_policy": "7-day return",
        "warranty": "1 year",
        "source_url": "https://example.com/iphone15",
        "affiliate_url": "https://example.com/affiliate/iphone15",
        "source_type": "live",
    }]

    result = normalize_provider_results(provider, payload)

    assert len(result) == 1
    item = result[0]
    assert isinstance(item, CanonicalProduct)
    assert item.provider == "ExampleProvider"
    assert item.title == "Apple iPhone 15"
    assert item.price == 69999
    assert item.currency == "INR"
    assert item.source_type == "live"
    assert item.confidence == 0.9
