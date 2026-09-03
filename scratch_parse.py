import sys, json, glob
sys.path.append('backend')
from app.connectors.blinkit import BlinkitConnector
from app.connectors.zepto import ZeptoConnector
from app.connectors.bigbasket import BigBasketConnector

registry = {
    'blinkit': BlinkitConnector(),
    'zepto': ZeptoConnector(),
    'bigbasket': BigBasketConnector()
}

import collections
results = collections.defaultdict(dict)

for file in glob.glob('backend/tests/fixtures/scraper_certification/runs/MATRIX/*.json'):
    with open(file, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    provider_name = data['provider'].lower()
    provider = registry.get(provider_name)
    if not provider: continue
    parsed = provider.parse_search_results(data['payload'])
    
    query = data['payload']['query'] if 'query' in data['payload'] else file.split('_')[-1].replace('.json', '')
    # For zepto the query is not in payload directly like that, let's just use the filename prefix
    
    first = parsed[0].name if parsed else "NO_ITEMS"
    results[provider_name][file.split('\\\\')[-1]] = first

print("ORACLE_MAPPING = {")
for prov, files in results.items():
    for f, first_item in files.items():
        print(f'    ("{prov}", "{f}"): "{first_item}",')
print("}")
