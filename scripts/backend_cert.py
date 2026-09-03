"""
Backend API Certification — proves what data would flow to the UI.
Tests all 8 categories via HTTP against the running backend.
"""
import json, sys, urllib.request, urllib.error
from datetime import datetime

BASE = "http://localhost:8000/api/v1"
RUN_ID = "run_20260826_150014"
OUT_DIR = f"artifacts/mobile_ui_certification/{RUN_ID}"

def call(path, method="GET", body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return {"error": e.reason, "code": e.code}, e.code
    except Exception as e:
        return {"error": str(e)}, 0

results = {}

print("=" * 64)
print(" TRUECOST BACKEND API CERTIFICATION")
print(f" Run: {RUN_ID}")
print("=" * 64)

# 1. Health
h, _ = call("/health".replace("/api/v1",""))
print(f"\n[HEALTH] {h}")

# 2. Backend /search for each category (cold, no data yet)
print("\n[1] COLD SEARCH — each category (no ingested data yet)")
categories = ["Grocery","Food","Pharmacy","Shopping","Mobility","Travel","Finance","Productivity"]
for cat in categories:
    data, status = call(f"/aggregator/search?q=test&category={cat}")
    primary = data.get("primary_results", [])
    pending = data.get("providers_pending", [])
    source = data.get("data_source", "db")
    print(f"  {cat:<14} status={status}  primary={len(primary)}  source={source}")
    results[cat] = {"cold_search_status": status, "primary_count": len(primary)}

# 3. Simulate a Grocery ingest (Red Bull from Blinkit real fixture)
print("\n[2] INGEST SIMULATION — Blinkit Red Bull real fixture data")
import os
MATRIX = "backend/tests/fixtures/scraper_certification/runs/MATRIX"
fixture = os.path.join(MATRIX, "blinkit_common_redbull.json")
if os.path.exists(fixture):
    with open(fixture) as f:
        d = json.load(f)
    ingest_body = {
        "provider": "Blinkit",
        "query": "Red Bull",
        "category": "Grocery",
        "raw_data": d.get("payload", {}),
        "search_session_id": None
    }
    resp, status = call("/aggregator/ingest", method="POST", body=ingest_body)
    sid = resp.get("search_session_id") or resp.get("session_id")
    print(f"  Ingest status: {status}")
    print(f"  Session ID: {sid}")
    print(f"  Products ingested: {resp.get('products_ingested', resp.get('items_ingested', '?'))}")
    
    # 3b. Now ingest Zepto
    fixture2 = os.path.join(MATRIX, "zepto_common_redbull.json")
    if os.path.exists(fixture2):
        with open(fixture2) as f:
            d2 = json.load(f)
        ingest_body2 = {
            "provider": "Zepto",
            "query": "Red Bull",
            "category": "Grocery",
            "raw_data": d2.get("payload", {}),
            "search_session_id": sid
        }
        resp2, _ = call("/aggregator/ingest", method="POST", body=ingest_body2)
        print(f"  Zepto ingest: {resp2.get('products_ingested', resp2.get('items_ingested', '?'))} products, session={sid}")

    # 3c. Ingest BigBasket
    fixture3 = os.path.join(MATRIX, "bigbasket_common_redbull.json")
    if os.path.exists(fixture3):
        with open(fixture3) as f:
            d3 = json.load(f)
        ingest_body3 = {
            "provider": "BigBasket",
            "query": "Red Bull",
            "category": "Grocery",
            "raw_data": d3.get("payload", {}),
            "search_session_id": sid
        }
        resp3, _ = call("/aggregator/ingest", method="POST", body=ingest_body3)
        print(f"  BigBasket ingest: {resp3.get('products_ingested', resp3.get('items_ingested', '?'))} products")

    # 3d. Query with session
    if sid:
        print(f"\n[3] SEARCH WITH SESSION — Red Bull / Grocery / session={sid[:12]}...")
        search, scode = call(f"/aggregator/search?q=Red+Bull&category=Grocery&session_id={sid}")
        primary = search.get("primary_results", [])
        providers = search.get("providers_responded", [])
        pending = search.get("providers_pending", [])
        print(f"  HTTP {scode}")
        print(f"  primary_results: {len(primary)}")
        print(f"  providers_responded: {providers}")
        print(f"  providers_pending: {pending}")
        
        # Save backend truth manifest
        manifest = {
            "run_id": RUN_ID,
            "case_id": "G2_redbull_3provider",
            "category": "Grocery",
            "query": "Red Bull",
            "session_id": sid,
            "backend_response": {
                "primary_results_count": len(primary),
                "providers_responded": providers,
                "providers_pending": pending,
            },
            "top_results": []
        }
        
        for p in primary[:5]:
            prices = p.get("prices", [])
            best_price = min([pr.get("price",9999) for pr in prices]) if prices else None
            manifest["top_results"].append({
                "name": p.get("name",""),
                "brand": p.get("brand",""),
                "weight_volume": p.get("weight_volume",""),
                "prices": [{
                    "provider": pr.get("provider",""),
                    "price": pr.get("price",""),
                    "delivery_time": pr.get("delivery_time",""),
                } for pr in prices]
            })
            print(f"  -> {p.get('name','')[:40]} | best Rs.{best_price} | providers: {[pr.get('provider','') for pr in prices]}")
        
        with open(f"{OUT_DIR}/grocery/case_manifest_G2.json", "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"  Manifest saved: grocery/case_manifest_G2.json")
        results["Grocery"]["session_search_status"] = scode
        results["Grocery"]["primary_count_with_session"] = len(primary)
        results["Grocery"]["providers_responded"] = providers

else:
    print("  FIXTURE NOT FOUND — cannot simulate grocery ingest")

# 4. Mobility endpoint
print("\n[4] MOBILITY ENDPOINT — /mobility/compare")
mob_body = {
    "pickup_lat": 12.9716, "pickup_lng": 77.5946,
    "drop_lat": 12.9784, "drop_lng": 77.6408,
    "ride_class": "standard", "objective": "cheapest"
}
mob_resp, mob_status = call("/mobility/compare", method="POST", body=mob_body)
print(f"  HTTP {mob_status}")
offers = mob_resp.get("offers", mob_resp.get("results", []))
print(f"  Offers returned: {len(offers)}")
if offers:
    for o in offers[:4]:
        print(f"  -> {o.get('provider',''):<10} Rs.{o.get('fare', o.get('price','?'))}")
results["Mobility"]["api_status"] = mob_status
results["Mobility"]["offers_count"] = len(offers)

# 5. Travel endpoint
print("\n[5] TRAVEL ENDPOINT — /travel/search")
trav_body = {"origin": "DEL", "destination": "BOM", "travel_date": "2026-09-15", "passengers": 1}
trav_resp, trav_status = call("/travel/search", method="POST", body=trav_body)
print(f"  HTTP {trav_status}")
flights = trav_resp.get("results", trav_resp.get("flights", []))
print(f"  Flights returned: {len(flights)}")
results["Travel"]["api_status"] = trav_status
results["Travel"]["flights_count"] = len(flights)

# Summary
print("\n" + "=" * 64)
print(" BACKEND API CERTIFICATION SUMMARY")
print("=" * 64)
with open(f"{OUT_DIR}/summary/backend_api_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f" Results saved to {OUT_DIR}/summary/backend_api_results.json")
print()
for cat, r in results.items():
    print(f"  {cat:<14}: {r}")
