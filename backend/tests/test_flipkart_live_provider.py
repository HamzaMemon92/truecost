from __future__ import annotations

import pytest

from app.config import settings
from app.providers.flipkart_provider import FlipkartProvider


@pytest.mark.asyncio
async def test_flipkart_live_provider_parses_real_affiliate_payload(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    async def fake_get(self, url, params=None, headers=None, timeout=None):
        assert "affiliate-api.flipkart.net" in url
        assert headers["Fk-Affiliate-Id"] == "affiliate-id"
        assert headers["Fk-Affiliate-Token"] == "affiliate-token"
        return FakeResponse({
            "productInfoList": [
                {
                    "productBaseInfoV1": {
                        "productId": "FLIPKART-123",
                        "title": "Apple MacBook Air M3",
                        "productBrand": "Apple",
                        "categoryPath": "Electronics > Laptops > Apple Laptops",
                        "productUrl": "https://www.flipkart.com/apple-macbook-air-m3/p/itm123",
                        "maximumRetailPrice": {"amount": 119999},
                        "sellingPrice": {"amount": 99999},
                        "averageRating": "4.8",
                        "ratings": "2100",
                        "inStock": "true",
                        "offers": ["Bank Offer", "Exchange Discount"],
                    }
                }
            ]
        })

    monkeypatch.setattr(settings, "flipkart_affiliate_id", "affiliate-id")
    monkeypatch.setattr(settings, "flipkart_affiliate_token", "affiliate-token")
    monkeypatch.setattr("app.providers.flipkart_provider.httpx.AsyncClient.get", fake_get)

    result = await FlipkartProvider().search("MacBook Air M3")

    assert len(result) == 1
    item = result[0]
    assert item.provider == "Flipkart"
    assert item.title == "Apple MacBook Air M3"
    assert item.brand == "Apple"
    assert item.category == "Electronics > Laptops > Apple Laptops"
    assert item.price == 99999.0
    assert item.currency == "INR"
    assert item.availability == "In stock"
    assert item.rating == 4.8
    assert item.review_count == 2100
    assert "Bank Offer" in item.offers
    assert item.source_type == "live"
