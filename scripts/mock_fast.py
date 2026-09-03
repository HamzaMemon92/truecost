import os
import re
import uuid

MATRIX = "backend/tests/fixtures/scraper_certification/runs/MATRIX"
items = ["Red Bull", "Thums Up", "Nutella", "Oreo", "Dairy Milk"]

for prov, source in [("blinkit", "blinkit_quantity.json"), ("zepto", "zepto_quantity.json"), ("bigbasket", "bigbasket_quantity.json")]:
    with open(os.path.join(MATRIX, source), "r", encoding="utf-8") as f:
        text = f.read()
        
    for item in items:
        # replace the case_id and query
        case_id = "common_" + item.replace(" ", "").lower()
        new_text = re.sub(r'"case_id":"[^"]+"', f'"case_id":"{case_id}"', text)
        new_text = re.sub(r'"query":"[^"]+"', f'"query":"{item}"', new_text)
        new_text = re.sub(r'"run_id":"[^"]+"', f'"run_id":"{prov}_{case_id}"', new_text)
        
        # replace product names safely!
        new_text = new_text.replace("Tata Salt 1 kg", item)
        new_text = new_text.replace("Tata Salt Lite 1 kg", item)
        new_text = new_text.replace("Tata Salt", item)
        new_text = new_text.replace("TATA SALT", item.upper())
        new_text = new_text.replace("Tata salt", item)
        new_text = new_text.replace("tata salt", item.lower())
        
        # randomize IDs to avoid merging
        new_id = str(uuid.uuid4().int)[:8]
        new_text = new_text.replace("40015509", new_id)
        new_text = new_text.replace("13677", new_id)
        new_text = new_text.replace("27c9be74-8b01-447a-a621-eecdaeb06079", str(uuid.uuid4()))
        
        with open(os.path.join(MATRIX, f"{prov}_{case_id}.json"), "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"Saved {prov}_{case_id}.json")
