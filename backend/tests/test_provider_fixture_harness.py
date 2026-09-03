from __future__ import annotations

from urllib.parse import urlparse

import pytest

from app.connectors.bigbasket import BigBasketConnector
from app.connectors.blinkit import BlinkitConnector
from app.connectors.swiggy import SwiggyInstamartConnector
from app.connectors.zepto import ZeptoConnector
from tests.provider_fixture_harness import expected_product, fixture_entries, load_fixture_payload, load_manifest


CONNECTORS = {
    "blinkit": BlinkitConnector(),
    "zepto": ZeptoConnector(),
    "swiggy": SwiggyInstamartConnector(),
    "bigbasket": BigBasketConnector(),
}


def _offer(product):
    assert product.prices, f"{product.id} has no provider offers"
    return product.prices[0]


def _valid_url(value: str | None) -> bool:
    parsed = urlparse(value or "")
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def test_fixture_manifest_declares_required_metadata() -> None:
    manifest = load_manifest()

    assert manifest["schema_version"] == "truecost.provider-fixture-manifest.v1"
    assert manifest["fixtures"]
    for entry in manifest["fixtures"]:
        for key in (
            "provider",
            "category",
            "query",
            "pincode",
            "latitude",
            "longitude",
            "captured_at",
            "source",
            "payload_file",
            "expected_products",
            "real_provider_notes",
        ):
            assert entry.get(key) not in (None, "", []), f"{entry.get('payload_file')} missing {key}"
        assert entry["source"] in {"synthetic", "captured"}


@pytest.mark.parametrize("entry", fixture_entries(), ids=lambda entry: entry["provider"])
def test_grocery_provider_fixture_parses_expected_offer(entry) -> None:
    connector = CONNECTORS[entry["provider"]]
    products = connector.parse_search_results(load_fixture_payload(entry))
    expected = expected_product(entry)

    assert products, f"{entry['provider']} fixture produced no products"
    product = products[0]
    offer = _offer(product)

    assert expected["name_contains"].casefold() in product.name.casefold()
    assert offer.provider == expected["provider"]
    assert offer.price == expected["price"]
    assert offer.price > 0
    assert offer.price < 100000
    assert offer.original_price == expected["original_price"]
    assert product.weight_volume == expected["weight_volume"]
    if expected.get("deep_link_required"):
        assert _valid_url(offer.deep_link), f"{entry['provider']} did not produce a valid product URL"


@pytest.mark.parametrize("entry", fixture_entries(), ids=lambda entry: entry["provider"])
def test_grocery_provider_fixture_does_not_emit_duplicate_products(entry) -> None:
    products = CONNECTORS[entry["provider"]].parse_search_results(load_fixture_payload(entry))
    fingerprints = {
        (product.id, product.name.casefold().strip(), product.weight_volume.casefold().strip())
        for product in products
    }

    assert len(fingerprints) == len(products)


def test_provider_handoff_contract_prefers_exact_product_urls_when_fixture_supports_them() -> None:
    for entry in fixture_entries():
        expected = expected_product(entry)
        if not expected.get("deep_link_required"):
            continue
        products = CONNECTORS[entry["provider"]].parse_search_results(load_fixture_payload(entry))
        offer = _offer(products[0])

        assert _valid_url(offer.deep_link)
        assert urlparse(offer.deep_link or "").path not in {"", "/"}


def test_provider_handoff_contract_has_explicit_confidence_fields() -> None:
    entry = fixture_entries(provider="blinkit")[0]
    product = CONNECTORS["blinkit"].parse_search_results(load_fixture_payload(entry))[0]
    offer = _offer(product)

    assert offer.product_url
    assert offer.fallback_search_url
    assert offer.handoff_confidence in {"exact_product", "search", "app_home"}


def test_provider_offers_preserve_availability_when_payload_supports_it() -> None:
    payload = {
        "products": [
            {
                "id": "bb-availability-1",
                "desc": "True Elements Muesli Fruit and Nuts",
                "brand": {"name": "True Elements"},
                "w": "1 kg",
                "aps": {"sp": 485, "mrp": 600},
                "availability": {"short_eta": "19 mins", "avail_status": "001", "availability_status": "available"},
            }
        ]
    }

    offer = BigBasketConnector().parse_search_results(payload)[0].prices[0]
    assert offer.in_stock is True
    assert offer.serviceable is True


def test_bigbasket_legacy_payload_prefers_shelf_price_over_member_price() -> None:
    payload = {
        "products": [
            {
                "id": "bb-legacy-1",
                "desc": "True Elements Muesli Fruit and Nuts",
                "brand": {"name": "True Elements"},
                "w": "1 kg",
                "aps": {"cp": 171, "sp": 485, "mrp": 600},
            }
        ]
    }

    product = BigBasketConnector().parse_search_results(payload)[0]
    assert product.prices[0].price == 485


def test_zepto_rupee_price_payload_is_not_divided_as_paise() -> None:
    entry = fixture_entries(provider="zepto")[0]
    payload = load_fixture_payload(entry)
    item = payload["layout"][0]["data"]["resolver"]["data"]["items"][0]["productResponse"]
    item["sellingPrice"] = 411
    item["mrp"] = 500

    product = ZeptoConnector().parse_search_results(payload)[0]
    assert product.prices[0].price == 411


def test_zepto_flat_webview_fallback_products_are_parsed() -> None:
    payload = {
        "products": [
            {
                "name": "Amul Gold Full Cream Fresh Milk | Pouch",
                "sp": 34,
                "mrp": 36,
                "unit": "1 pack (500 ml)",
                "img_url": "https://cdn.example.test/amul-gold-500ml.png",
                "nav_id": "zepto-500ml",
                "url": "https://www.zepto.com/pn/amul-gold-full-cream-fresh-milk/pvid/zepto-500ml",
                "in_stock": True,
            }
        ]
    }

    product = ZeptoConnector().parse_search_results(payload)[0]
    offer = product.prices[0]

    assert product.name == "Amul Gold Full Cream Fresh Milk | Pouch"
    assert product.weight_volume == "1 pack (500 ml)"
    assert product.provider_sku == "zepto-500ml"
    assert product.image_url == "https://cdn.example.test/amul-gold-500ml.png"
    assert offer.provider == "Zepto"
    assert offer.price == 34
    assert offer.original_price == 36
    assert offer.in_stock is True
    assert offer.product_url == "https://www.zepto.com/pn/amul-gold-full-cream-fresh-milk/pvid/zepto-500ml"
