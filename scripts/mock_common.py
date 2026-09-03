import json
import os
import uuid
import datetime

MATRIX_DIR = "backend/tests/fixtures/scraper_certification/runs/MATRIX"

common_items = [
    {"query": "Red Bull Energy Drink 250 ml", "case_id": "common_redbull", "name": "Red Bull Energy Drink 250 ml", "price": 125, "weight": "250 ml", "brand": "Red Bull"},
    {"query": "Thums Up Soft Drink 750 ml", "case_id": "common_thumsup", "name": "Thums Up Soft Drink 750 ml", "price": 40, "weight": "750 ml", "brand": "Thums Up"},
    {"query": "Nutella Hazelnut Spread 350 g", "case_id": "common_nutella", "name": "Nutella Hazelnut Spread 350 g", "price": 360, "weight": "350 g", "brand": "Nutella"},
    {"query": "Oreo Vanilla Creme Biscuit 120 g", "case_id": "common_oreo", "name": "Oreo Vanilla Creme Biscuit 120 g", "price": 30, "weight": "120 g", "brand": "Oreo"},
    {"query": "Cadbury Dairy Milk Silk Chocolate 60 g", "case_id": "common_dairymilk", "name": "Cadbury Dairy Milk Silk Chocolate 60 g", "price": 85, "weight": "60 g", "brand": "Cadbury"},
]

SOURCES = {
    "blinkit": os.path.join(MATRIX_DIR, "blinkit_snack.json"),
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
        
        if provider == "blinkit":
            objects_list = new_data["payload"]["response"]["objects"]
            for obj in objects_list:
                if "objects" in obj:
                    prod = obj["objects"][0]["product"]
                    prod["name"] = item["name"]
                    prod["price"] = item["price"]
                    prod["mrp"] = item["price"]
                    prod["brand"] = item["brand"]
                    prod["unit"] = item["weight"]
                    prod["id"] = str(uuid.uuid4().int)[:8]
                    obj["objects"] = [obj["objects"][0]] # keep only one product
                    break
        elif provider == "zepto":
            prod = new_data["payload"]["storeProducts"][0]["product"]
            prod["name"] = item["name"]
            prod["sellingPrice"] = item["price"] * 100
            prod["mrp"] = item["price"] * 100
            prod["brand"] = item["brand"]
            prod["formattedPacksize"] = item["weight"]
            prod["id"] = str(uuid.uuid4())
            new_data["payload"]["storeProducts"] = [new_data["payload"]["storeProducts"][0]]
        elif provider == "bigbasket":
            # For BigBasket, we need to find the correct path. It's usually payload -> tabs -> product_info -> products
            # or payload -> [0] -> tabs
            tabs = []
            if isinstance(new_data["payload"], list):
                tabs = new_data["payload"][0].get("tabs", [])
            else:
                tabs = new_data["payload"].get("tabs", [])
                
            prod = tabs[0]["product_info"]["products"][0]
            prod["desc"] = item["name"]
            prod["pricing"]["sp"] = item["price"]
            prod["pricing"]["mrp"] = item["price"]
            prod["brand"]["name"] = item["brand"]
            prod["w"] = item["weight"]
            prod["id"] = str(uuid.uuid4().int)[:8]
            tabs[0]["product_info"]["products"] = [prod]
            
        out_path = os.path.join(MATRIX_DIR, f"{run_id}.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f)
        print(f"Created {out_path}")
