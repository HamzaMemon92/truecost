import json, os, glob
from datetime import datetime, timezone

MATRIX = 'backend/tests/fixtures/scraper_certification/runs/MATRIX'
ALL_CAT = 'backend/tests/fixtures/scraper_certification/runs/ALL_CATEGORIES'

matrix_files = glob.glob(f'{MATRIX}/*.json')
allcat_files = glob.glob(f'{ALL_CAT}/*.json')

provider_counts = {}
for f in matrix_files:
    base = os.path.basename(f)
    prefix = base.split('_')[0]
    provider_counts[prefix] = provider_counts.get(prefix, 0) + 1

print('MATRIX fixture counts:')
for k,v in sorted(provider_counts.items()):
    print(f'  {k}: {v}')
print(f'Total MATRIX: {len(matrix_files)}')
print(f'Total ALL_CATEGORIES: {len(allcat_files)}')

print()
print('Dishonest capture check:')
for fname in ['amazon_airpods.json','uber_mg_road.json','makemytrip_del_bom.json']:
    fpath = os.path.join(MATRIX, fname)
    d = json.load(open(fpath))
    mode = d.get('execution_mode', 'MISSING')
    print(f'  {fname}: {mode}')

print()
print('Hard gate violations:')
violations = 0
for fpath in matrix_files:
    d = json.load(open(fpath))
    cv = d.get('capture_version','')
    if cv != 'truecost.source.capture.v1':
        print(f'  BAD_VERSION: {os.path.basename(fpath)} -> {cv}')
        violations += 1
    payload_str = json.dumps(d.get('payload', {}))
    if 'userSessionId' in payload_str and '[REDACTED]' not in payload_str:
        print(f'  UNSANITIZED_PII: {os.path.basename(fpath)}')
        violations += 1

for fpath in allcat_files:
    d = json.load(open(fpath))
    em = d.get('execution_mode','')
    if em == 'REAL_LIVE_SCRAPE':
        print(f'  FALSE_REAL_SCRAPE: {os.path.basename(fpath)}')
        violations += 1

print(f'Total violations: {violations}')
if violations == 0:
    print('ALL HARD GATES: PASS')
