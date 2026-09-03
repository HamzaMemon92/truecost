import sys
sys.path.insert(0, '.')
import json, os

from app.connectors.uber import UberConnector
from app.connectors.ola import OlaConnector
from app.connectors.rapido import RapidoConnector
from app.connectors.blinkit import BlinkitConnector
from app.connectors.zepto import ZeptoConnector
from app.connectors.bigbasket import BigBasketConnector
from app.connectors.zomato import ZomatoConnector
from app.connectors.tata1mg import Tata1mgConnector
from app.connectors.makemytrip import MakeMyTripConnector
from app.connectors.bankbazaar import BankBazaarConnector
from app.services.entity_resolution import entity_resolution_service
from app.graph.transit_workflow import compile_transit_workflow
from app.graph.food_pharmacy_workflow import compile_food_pharmacy_workflow
from app.graph.evaluation_workflow import compile_evaluation_workflow

print("=" * 64)
print(" TRUECOST — ELITE FULL-SYSTEM VERIFICATION REPORT")
print("=" * 64)

# 1. ENTITY RESOLUTION
print()
print("[1] ENTITY RESOLUTION SUPPORT (all 8 categories)")
cats = ["grocery","shopping","food","pharmacy","mobility","travel","finance","productivity"]
er_pass = True
for c in cats:
    ok = entity_resolution_service.supports(c)
    if not ok: er_pass = False
    print(f"    {c:<16} {'PASS' if ok else 'FAIL'}")
print(f"    Result: {'ALL PASS' if er_pass else 'SOME FAIL'}")

# 2. MOBILITY CROSS-PROVIDER
print()
print("[2] MOBILITY — Uber vs Ola vs Rapido (cross-provider price ranking)")
u = UberConnector().parse_search_results({"rides": [
    {"id":"go","name":"UberGo","fare":{"amount":245},"eta_seconds":240},
    {"id":"moto","name":"UberMoto","fare":{"amount":85},"eta_seconds":120},
]})
o = OlaConnector().parse_search_results({"serviceTypes": [
    {"id":"mini","name":"Ola Mini","pricing":{"currencyAmount":180},"eta":5},
    {"id":"auto","name":"Ola Auto","pricing":{"currencyAmount":95},"eta":3},
]})
r = RapidoConnector().parse_search_results({"rides": [
    {"name":"Bike","fare":65,"eta":7,"vehicleType":"bike"},
    {"name":"Auto","fare":90,"eta":5,"vehicleType":"auto"},
]})
mob = sorted(u + o + r, key=lambda p: p.prices[0].price if p.prices else 9999)
for i, p in enumerate(mob):
    pr = p.prices[0].price
    pv = p.prices[0].provider
    eta = p.prices[0].delivery_time
    tag = " <- WINNER (cheapest)" if i == 0 else ""
    print(f"    {pv:<8} {p.name:<16} Rs.{pr:<6} {eta}{tag}")
saving = mob[-1].prices[0].price - mob[0].prices[0].price
print(f"    User saves Rs.{saving} vs most expensive option")

# 3. GROCERY CROSS-PROVIDER (real data)
print()
print("[3] GROCERY — Red Bull across Blinkit / Zepto / BigBasket (real MATRIX data)")
MATRIX = "tests/fixtures/scraper_certification/runs/MATRIX"
groc = []
for fname, ConnCls, label in [
    ("blinkit_common_redbull.json", BlinkitConnector, "Blinkit"),
    ("zepto_common_redbull.json", ZeptoConnector, "Zepto"),
    ("bigbasket_common_redbull.json", BigBasketConnector, "BigBasket"),
]:
    fpath = os.path.join(MATRIX, fname)
    if os.path.exists(fpath):
        d = json.load(open(fpath))
        items = ConnCls().parse_search_results(d.get("payload", {}))
        if items:
            groc.append(items[0])
            name_trunc = items[0].name[:35]
            price = items[0].prices[0].price if items[0].prices else 0
            print(f"    {label:<12} '{name_trunc}'  Rs.{price}")
        else:
            print(f"    {label:<12} 0 items parsed from fixture")
    else:
        print(f"    {label:<12} fixture not found")
if groc:
    groc_ranked = sorted(groc, key=lambda p: p.prices[0].price if p.prices else 9999)
    winner = groc_ranked[0]
    print(f"    BEST PRICE: {winner.prices[0].provider} at Rs.{winner.prices[0].price}")

# 4. LANGGRAPH WORKFLOWS
print()
print("[4] LANGGRAPH WORKFLOWS — end-to-end invocation")

wf = compile_transit_workflow()
state = {"origin": "MG Road", "destination": "Indiranagar", "mode": "mobility",
         "query": "MG Road to Indiranagar", "options": [], "recommendation": {}, "provider_network_calls": 0}
out = wf.invoke(state)
rec = out.get("recommendation", {})
print(f"    transit_workflow     : OK — recommendation keys: {list(rec.keys())}")

wf2 = compile_food_pharmacy_workflow()
state2 = {"query": "Pizza", "category": "food", "items": [], "ranked_options": [], "errors": [], "provider_network_calls": 0}
out2 = wf2.invoke(state2)
print(f"    food_pharmacy_wf     : OK — ranked_options count: {len(out2.get('ranked_options', []))}")

wf3 = compile_evaluation_workflow()
state3 = {"requirements": "Credit card", "domain": "finance", "query": "", "candidates": [], "comparison_matrix": {}, "provider_network_calls": 0}
out3 = wf3.invoke(state3)
print(f"    evaluation_wf        : OK — comparison_matrix: {out3.get('comparison_matrix', {})}")

# 5. CERTIFICATION TEST SUITE
print()
print("[5] CERTIFICATION TEST SUITE")
import subprocess
result = subprocess.run(
    ["python", "-m", "pytest", "tests/certification/", "-q", "--tb=no", "--ignore=tests/test_grocery_certification_matrix.py"],
    capture_output=True, text=True
)
last = [l for l in result.stdout.strip().split("\n") if l.strip()][-1] if result.stdout else "no output"
print(f"    {last}")

print()
print("=" * 64)
print(" VERIFICATION COMPLETE")
print("=" * 64)
