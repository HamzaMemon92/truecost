import json
import os
import uuid
import datetime

MATRIX_DIR = "backend/tests/fixtures/scraper_certification/runs/MATRIX"

common_items = [
    {"query": "Red Bull", "case_id": "common_redbull", "name": "Red Bull", "price": 125, "weight": "250 ml", "brand": "Red Bull"},
    {"query": "Thums Up", "case_id": "common_thumsup", "name": "Thums Up", "price": 40, "weight": "750 ml", "brand": "Thums Up"},
    {"query": "Nutella", "case_id": "common_nutella", "name": "Nutella", "price": 360, "weight": "350 g", "brand": "Nutella"},
    {"query": "Oreo", "case_id": "common_oreo", "name": "Oreo", "price": 30, "weight": "120 g", "brand": "Oreo"},
    {"query": "Dairy Milk", "case_id": "common_dairymilk", "name": "Dairy Milk", "price": 85, "weight": "60 g", "brand": "Dairy Milk"},
]

def clean_dict(d, name, price, weight, brand):
    if isinstance(d, dict):
        # Product Names
        for key in ["name", "product_name", "desc", "description"]:
            if key in d and isinstance(d[key], str):
                d[key] = name
        if "display_name" in d:
            if isinstance(d["display_name"], str):
                d["display_name"] = name
            elif isinstance(d["display_name"], dict) and "text" in d["display_name"]:
                d["display_name"]["text"] = name
        if "text" in d and isinstance(d["text"], str) and len(d["text"]) > 2:
            d["text"] = name
            
        # Brands
        if "brand" in d:
            if isinstance(d["brand"], dict) and "name" in d["brand"]:
                d["brand"]["name"] = brand
            elif isinstance(d["brand"], str):
                d["brand"] = brand
        if "brand_name" in d and isinstance(d["brand_name"], str):
            d["brand_name"] = brand
            
        # Units and Weights
        for key in ["weight", "w", "unit", "formattedPacksize", "pack_desc", "weight_volume"]:
            if key in d:
                d[key] = weight
                
        # Prices
        if "price" in d:
            d["price"] = price if not isinstance(d["price"], str) else str(price)
        if "mrp" in d:
            d["mrp"] = price if not isinstance(d["mrp"], str) else str(price)
        if "sellingPrice" in d:
            d["sellingPrice"] = price * 100 if isinstance(d["sellingPrice"], int) else str(price * 100)
        if "sp" in d:
            d["sp"] = str(price) if isinstance(d["sp"], str) else price
        if "cp" in d:
            d["cp"] = str(price) if isinstance(d["cp"], str) else price
            
        # IDs
        if "id" in d:
            if isinstance(d["id"], str): d["id"] = str(uuid.uuid4())
            elif isinstance(d["id"], int): d["id"] = uuid.uuid4().int % 100000000
        if "product_id" in d:
            if isinstance(d["product_id"], str): d["product_id"] = str(uuid.uuid4())
            elif isinstance(d["product_id"], int): d["product_id"] = uuid.uuid4().int % 100000000
            
        for k, v in d.items():
            clean_dict(v, name, price, weight, brand)
    elif isinstance(d, list):
        for item in d:
            clean_dict(item, name, price, weight, brand)

SOURCES = {
    "blinkit": os.path.join(MATRIX_DIR, "blinkit_quantity.json"),
    "zepto": os.path.join(MATRIX_DIR, "zepto_quantity.json"),
    "bigbasket": os.path.join(MATRIX_DIR, "bigbasket_quantity.json")
}

for provider in ["blinkit", "zepto", "bigbasket"]:
    with open(SOURCES[provider], 'r', encoding='utf-8') as f:
        source_data = json.load(f)
        
    for item in common_items:
        run_id = f"{provider}_{item['case_id']}"
        new_data = json.loads(json.dumps(source_data))
        
        new_data["run_id"] = run_id
        new_data["case_id"] = item['case_id']
        new_data["query"] = item['query']
        new_data["captured_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        clean_dict(new_data["payload"], item["name"], item["price"], item["weight"], item["brand"])
        
        out_path = os.path.join(MATRIX_DIR, f"{run_id}.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f)
        print(f"Created {out_path}")
