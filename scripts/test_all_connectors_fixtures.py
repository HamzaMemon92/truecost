import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.api.endpoints.aggregator import connectors

FIXTURES_BASE = "backend/tests/fixtures/scraper_certification/runs/ALL_CATEGORIES"
files = [f for f in os.listdir(FIXTURES_BASE) if f.endswith(".json")]

parsed_ok = 0
failed = []

for f in files:
    path = os.path.join(FIXTURES_BASE, f)
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    prov = data["provider"]
    connector = connectors.get(prov)
    if not connector:
        failed.append((f, f"Missing connector for {prov}"))
        continue
    try:
        res = connector.parse_search_results(data["payload"])
        if len(res) > 0:
            parsed_ok += 1
        else:
            failed.append((f, "Empty parsed list"))
    except Exception as e:
        failed.append((f, str(e)))

print(f"Total fixtures: {len(files)}")
print(f"Successfully parsed: {parsed_ok}")
print(f"Failed count: {len(failed)}")
if failed:
    print("Failures:")
    for fn, err in failed[:10]:
        print(f"  {fn}: {err}")
