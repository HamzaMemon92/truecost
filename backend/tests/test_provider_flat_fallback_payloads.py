from app.connectors.blinkit import BlinkitConnector
from app.connectors.swiggy import SwiggyInstamartConnector


def test_blinkit_nested_payload_uses_id_when_product_id_absent():
    products = BlinkitConnector().parse_search_results({
        "cart_item": {
            "id": "item123",
            "product_name": "Amul Taaza Toned Fresh Milk",
            "price": 30,
            "mrp": 32,
            "unit": "500 ml",
        }
    })

    assert len(products) == 1
    assert products[0].id == "tc_blinkit_item123"
    assert products[0].prices[0].fallback_search_url.endswith("Amul+Taaza+Toned+Fresh+Milk")


def test_blinkit_generic_nested_product_payload_is_parsed():
    products = BlinkitConnector().parse_search_results({
        "layout": {
            "widgets": [
                {
                    "type": "product-card",
                    "data": {
                        "productId": "12345",
                        "variantId": "v500",
                        "displayName": "Amul Gold Full Cream Milk",
                        "brandName": "Amul",
                        "formattedPacksize": "500 ml",
                        "pricing": {"sellingPrice": 36, "mrp": 38},
                        "availability": {"inStock": True},
                        "images": [{"url": "https://cdn.test/blinkit-amul-gold-500ml.jpg"}],
                        "productUrl": "https://blinkit.com/prn/amul-gold/prid/12345",
                    },
                }
            ]
        }
    })

    assert len(products) == 1
    product = products[0]
    assert product.name == "Amul Gold Full Cream Milk"
    assert product.brand == "Amul"
    assert product.weight_volume == "500 ml"
    assert product.prices[0].price == 36
    assert product.prices[0].in_stock is True
    assert product.image_url == "https://cdn.test/blinkit-amul-gold-500ml.jpg"


def test_swiggy_flat_dom_fallback_payload_is_parsed():
    products = SwiggyInstamartConnector().parse_search_results({
        "products": [
            {
                "name": "Amul Gold Full Cream Milk",
                "brand": "Amul",
                "sp": 36,
                "mrp": 38,
                "unit": "500 ml",
                "url": "https://www.swiggy.com/instamart/item/123",
            }
        ]
    })

    assert len(products) == 1
    product = products[0]
    assert product.name == "Amul Gold Full Cream Milk"
    assert product.brand == "Amul"
    assert product.weight_volume == "500 ml"
    assert product.prices[0].provider == "Swiggy Instamart"
    assert product.prices[0].price == 36
    assert product.prices[0].product_url == "https://www.swiggy.com/instamart/item/123"


def test_swiggy_nested_variants_are_expanded_as_distinct_skus():
    products = SwiggyInstamartConnector().parse_search_results({
        "data": {
            "cards": [{
                "displayName": "Amul Gold Homogenised Standardised Full Cream Milk",
                "brandName": "Amul",
                "imageIds": ["amul-gold"],
                "variations": [
                    {
                        "skuId": "swiggy-gold-1l",
                        "quantityDescription": "1 ltr",
                        "price": {"offerPrice": {"units": 83}, "mrp": {"units": 83}},
                    },
                    {
                        "skuId": "swiggy-gold-12x1l",
                        "quantityDescription": "1 ltr x 12",
                        "price": {"offerPrice": {"units": 996}, "mrp": {"units": 996}},
                    },
                    {
                        "skuId": "swiggy-gold-500ml",
                        "quantityDescription": "500 ml",
                        "price": {"offerPrice": {"units": 36}, "mrp": {"units": 36}},
                    },
                ],
            }]
        }
    })

    by_size = {product.weight_volume: product for product in products}
    assert {"500 ml", "1 ltr", "1 ltr x 12"}.issubset(by_size)
    assert by_size["500 ml"].name == "Amul Gold Homogenised Standardised Full Cream Milk"
    assert by_size["500 ml"].prices[0].price == 36


def test_swiggy_nested_variants_do_not_inherit_parent_image_when_variant_image_missing():
    products = SwiggyInstamartConnector().parse_search_results({
        "data": {
            "cards": [{
                "displayName": "Amul Gold Homogenised Standardised Full Cream Milk",
                "brandName": "Amul",
                "imageIds": ["parent-1l-tetra-image"],
                "variations": [
                    {
                        "skuId": "swiggy-gold-500ml",
                        "quantityDescription": "500 ml",
                        "price": {"offerPrice": {"units": 36}, "mrp": {"units": 36}},
                    },
                    {
                        "skuId": "swiggy-gold-1l",
                        "quantityDescription": "1 ltr",
                        "imageIds": ["variant-1l-tetra-image"],
                        "price": {"offerPrice": {"units": 83}, "mrp": {"units": 83}},
                    },
                ],
            }]
        }
    })

    by_size = {product.weight_volume: product for product in products}
    assert by_size["500 ml"].image_url == ""
    assert by_size["500 ml"].unknown_attributes["image_match_status"] == "NO_IMAGE"
    assert by_size["1 ltr"].image_url.endswith("/variant-1l-tetra-image")
    assert by_size["1 ltr"].unknown_attributes["image_match_status"] == "EXACT_SKU_IMAGE"
