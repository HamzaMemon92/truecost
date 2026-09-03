import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from app.connectors.swiggy import SwiggyInstamartConnector

sample_instamart_payload = {
    "data": {
        "widgets": [
            {
                "data": [
                    {
                        "variations": [
                            {
                                "skuId": "swiggy_milk_001",
                                "displayName": "Amul Taaza Toned Fresh Milk",
                                "brand": "Amul",
                                "price": {"offerPrice": {"units": 68}, "mrp": {"units": 72}},
                                "imageIds": ["fl_lossy,f_auto,q_auto,w_288,h_360/sample_milk.jpg"],
                                "quantity": "1 L"
                            }
                        ]
                    }
                ]
            }
        ]
    }
}

connector = SwiggyInstamartConnector()
parsed = connector.parse_search_results(sample_instamart_payload)
print(f"Swiggy Connector parsed {len(parsed)} products successfully:")
for p in parsed:
    print(f"  ID: {p.id}")
    print(f"  Name: {p.name}")
    print(f"  Brand: {p.brand}")
    print(f"  Price: {p.prices[0].price if p.prices else 'None'}")
    print(f"  Original Price: {p.prices[0].original_price if p.prices else 'None'}")
    print(f"  Weight/Unit: {p.weight_volume}")
    print(f"  Deep link: {p.prices[0].deep_link if p.prices else 'None'}")
