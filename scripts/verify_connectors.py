import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import json
from app.connectors.blinkit import BlinkitConnector
from app.connectors.zepto import ZeptoConnector
from app.connectors.bigbasket import BigBasketConnector

b_c = BlinkitConnector()
z_c = ZeptoConnector()
bb_c = BigBasketConnector()

MATRIX_DIR = "backend/tests/fixtures/scraper_certification/runs/MATRIX"

for item in ["redbull", "thumsup", "nutella", "oreo", "dairymilk"]:
    print(f"=== {item} ===")
    b_file = os.path.join(MATRIX_DIR, f"blinkit_common_{item}.json")
    b_res = b_c.parse_search_results(json.load(open(b_file, encoding='utf-8'))['payload'])
    print("Blinkit:", [(p.name, p.brand, p.weight_volume, p.prices[0].price if p.prices else None) for p in b_res][:1])
    
    z_file = os.path.join(MATRIX_DIR, f"zepto_common_{item}.json")
    z_res = z_c.parse_search_results(json.load(open(z_file, encoding='utf-8'))['payload'])
    print("Zepto:", [(p.name, p.brand, p.weight_volume, p.prices[0].price if p.prices else None) for p in z_res][:1])
    
    bb_file = os.path.join(MATRIX_DIR, f"bigbasket_common_{item}.json")
    bb_res = bb_c.parse_search_results(json.load(open(bb_file, encoding='utf-8'))['payload'])
    print("BigBasket:", [(p.name, p.brand, p.weight_volume, p.prices[0].price if p.prices else None) for p in bb_res][:1])
