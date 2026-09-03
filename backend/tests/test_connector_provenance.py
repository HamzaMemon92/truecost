import pytest
from app.connectors.zepto import ZeptoConnector
from app.connectors.blinkit import BlinkitConnector
from app.connectors.bigbasket import BigBasketConnector
from app.connectors.swiggy import SwiggyInstamartConnector

def test_grocery_connectors_do_not_invent_delivery_estimates() -> None:
    cases = [
        (ZeptoConnector(), {"layout": [{"widgetId": "PRODUCT_GRID", "data": {"resolver": {"data": {"items": [{"productResponse": {"product": {"name": "Milk", "brand": "Test"}, "productVariant": {"images": [{"path": "x"}]}, "id": "1", "sellingPrice": 7200, "mrp": 7500}}]}}}}]}),
        (BlinkitConnector(), {"data": {"cart_item": {"product_id": "1", "product_name": "Milk", "brand": "Test", "price": 72, "mrp": 75}}}),
        (BigBasketConnector(), {"products": [{"id": "1", "desc": "Milk", "absolute_url": "x", "images": [{"name": "x"}], "brand": {"name": "Test"}, "aps": {"cp": 72, "mrp": 75}}]}),
        (SwiggyInstamartConnector(), {"data": {"widgets": [{"data": [{"product_id": "1", "displayName": "Milk", "brand": "Test", "price": {"offerPrice": {"units": 7200}, "mrp": {"units": 7500}}}]}]}}),
    ]
    for connector, payload in cases:
        products = connector.parse_search_results(payload)
        assert len(products) == 1, f"Connector {connector.provider_name} failed to parse 1 product"
        for p in products:
            for price in p.prices:
                assert price.delivery_time in (None, ""), f"Connector {connector.provider_name} invented ETA {price.delivery_time}"

def test_observed_delivery_estimate_is_preserved() -> None:
    cases = [
        (ZeptoConnector(), {"layout": [{"widgetId": "PRODUCT_GRID", "data": {"resolver": {"data": {"items": [{"productResponse": {"product": {"name": "Milk", "brand": "Test"}, "productVariant": {"images": [{"path": "x"}]}, "id": "1", "sellingPrice": 7200, "mrp": 7500}, "delivery_time": "12 mins"}]}}}}]}),
        (BlinkitConnector(), {"data": {"cart_item": {"product_id": "1", "product_name": "Milk", "brand": "Test", "price": 72, "mrp": 75, "delivery_time": "15 mins"}}}),
        (BigBasketConnector(), {"products": [{"id": "1", "desc": "Milk", "absolute_url": "x", "images": [{"name": "x"}], "brand": {"name": "Test"}, "aps": {"cp": 72, "mrp": 75}, "availability": {"short_eta": "8 mins"}}]}),
        (SwiggyInstamartConnector(), {"data": {"widgets": [{"data": [{"product_id": "1", "displayName": "Milk", "brand": "Test", "price": {"offerPrice": {"units": 7200}, "mrp": {"units": 7500}}, "delivery_time": "10 mins"}]}]}}),
    ]
    for connector, payload in cases:
        products = connector.parse_search_results(payload)
        assert len(products) == 1
        for p in products:
            for price in p.prices:
                assert price.delivery_time != "", f"Connector {connector.provider_name} dropped ETA"
