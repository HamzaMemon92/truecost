import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.providers.quickcommerce_provider import QuickCommerceProvider, _map_to_canonical, _parse_delivery_minutes

# ─── Unit: delivery parsing ────────────────────────────────────────────────────

def test_parse_delivery_minutes_variants():
    assert _parse_delivery_minutes("8 mins") == 8
    assert _parse_delivery_minutes("12 min") == 12
    assert _parse_delivery_minutes("15 minutes") == 15
    assert _parse_delivery_minutes("in ~20 min") == 20
    assert _parse_delivery_minutes(None) is None
    assert _parse_delivery_minutes("express") is None


# ─── Unit: schema mapping ──────────────────────────────────────────────────────

def test_map_to_canonical_full_payload():
    raw = {
        "id": "blinkit-amul-milk-500ml",
        "name": "Amul Taaza Toned Milk 500ml",
        "brand": "Amul",
        "category": "Dairy",
        "offer_price": 27,
        "mrp": 30,
        "platform": {"sla": "8 mins"},
        "available": True,
        "deeplink": "https://blinkit.com/p/amul-milk",
        "discount_label": "10% OFF",
        "quantity": "500 ml",
        "images": ["https://cdn.example.com/amul.jpg"],
    }
    item = _map_to_canonical(raw, "Blinkit", 12.97, 77.59)

    assert item is not None
    assert item.title == "Amul Taaza Toned Milk 500ml"
    assert item.provider == "Blinkit"
    assert item.price == 27.0
    assert item.availability == "In Stock"
    assert item.delivery_minutes == 8
    assert item.source_type == "live"
    assert item.provider_status == "active"
    assert "10% OFF" in item.offers
    assert item.confidence == 0.95


def test_map_to_canonical_out_of_stock():
    raw = {"id": "xyz", "name": "Some Product", "offer_price": 100, "available": False}
    item = _map_to_canonical(raw, "Zepto", 12.97, 77.59)
    assert item is not None
    assert item.availability == "Out of Stock"


def test_map_to_canonical_missing_name_returns_none():
    raw = {"id": "xyz", "offer_price": 100}
    item = _map_to_canonical(raw, "Zepto", 12.97, 77.59)
    assert item is None


# ─── Unit: provider feature flag ──────────────────────────────────────────────

def test_provider_disabled_without_key():
    with patch("app.providers.quickcommerce_provider.settings") as mock_settings:
        mock_settings.quickcommerce_api_key = None
        provider = QuickCommerceProvider()
        assert provider.is_enabled() is False


def test_provider_enabled_with_key():
    with patch("app.providers.quickcommerce_provider.settings") as mock_settings:
        mock_settings.quickcommerce_api_key = "sk_live_test_key"
        provider = QuickCommerceProvider()
        assert provider.is_enabled() is True


# ─── Integration: mocked HTTP fan-out ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_returns_empty_without_key():
    """No API key = no results, no crash."""
    with patch("app.providers.quickcommerce_provider.settings") as mock_settings:
        mock_settings.quickcommerce_api_key = None
        provider = QuickCommerceProvider()
        results = await provider.search("milk")
        assert results == []








@pytest.mark.asyncio
async def test_registry_includes_quickcommerce_when_key_set():
    """Registry returns QuickCommerce as first provider when key is configured."""
    with patch("app.providers.quickcommerce_provider.settings") as mock_settings:
        mock_settings.quickcommerce_api_key = "sk_live_test_key"

        from app.providers.grocery_registry import get_grocery_providers
        from app.providers.quickcommerce_provider import QuickCommerceProvider

        providers = get_grocery_providers()
        # QuickCommerce should be inserted at index 0 when enabled
        assert isinstance(providers[0], QuickCommerceProvider)


@pytest.mark.asyncio
async def test_registry_excludes_quickcommerce_when_no_key():
    """Registry should NOT include QuickCommerce when no key is set."""
    with patch("app.providers.quickcommerce_provider.settings") as mock_settings:
        mock_settings.quickcommerce_api_key = None

        from app.providers.grocery_registry import get_grocery_providers
        from app.providers.quickcommerce_provider import QuickCommerceProvider

        providers = get_grocery_providers()
        names = [type(p).__name__ for p in providers]
        assert "QuickCommerceProvider" not in names
