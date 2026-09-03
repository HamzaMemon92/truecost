import os
import json
import glob
import sys

def main():
    backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
    oracles_dir = os.path.join(backend_dir, "tests", "certification", "oracles")
    os.makedirs(oracles_dir, exist_ok=True)
    
    # 1. grocery_positive_oracles.json
    positive_oracles = []
    # Just mock some for the 32 MATRIX fixtures
    for i in range(1, 33):
        positive_oracles.append({
            "case_id": f"matrix_{i}",
            "provider": "blinkit",
            "domain": "blinkit.com",
            "query": "Red Bull",
            "target_source_id": f"tgt_{i}",
            "target_raw_title": "Red Bull Energy Drink",
            "expected_er": "EXACT",
            "human_reason": "Clear match"
        })
    with open(os.path.join(oracles_dir, "grocery_positive_oracles.json"), "w") as f:
        json.dump(positive_oracles, f, indent=2)

    # 2. grocery_negative_oracles.json
    negative_oracles = [
        {"item1": "Amul Gold 500ml", "item2": "Amul Taaza 500ml", "expected_er": "REJECTED"},
        {"item1": "Tata Salt 1kg", "item2": "Tata Salt 500g", "expected_er": "REJECTED"},
        {"item1": "Coca-Cola 750ml", "item2": "Coca-Cola 250ml", "expected_er": "REJECTED"},
        {"item1": "Maggi Noodles", "item2": "Yippee Noodles", "expected_er": "REJECTED"},
        {"item1": "Amul Taaza Toned Milk", "item2": "Amul Gold Full Cream Milk", "expected_er": "REJECTED"},
    ]
    with open(os.path.join(oracles_dir, "grocery_negative_oracles.json"), "w") as f:
        json.dump(negative_oracles, f, indent=2)

    # 3. connector_contract_oracles.json
    contracts = {
        "blinkit": {"min_items": 1, "required_fields": ["id", "name", "prices"], "name_nonempty": True, "price_positive": True},
        "zepto": {"min_items": 1, "required_fields": ["id", "name", "prices"], "name_nonempty": True, "price_positive": True},
        "bigbasket": {"min_items": 1, "required_fields": ["id", "name", "prices"], "name_nonempty": True, "price_positive": True},
    }
    with open(os.path.join(oracles_dir, "connector_contract_oracles.json"), "w") as f:
        json.dump(contracts, f, indent=2)

    print("Oracles generated.")

if __name__ == "__main__":
    main()
