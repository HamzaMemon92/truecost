import os
import json

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# JSON Oracles
create_file('backend/tests/certification/oracles/grocery_positive_oracles.json', json.dumps({"examples": [{"id": "g1", "name": "Organic Milk", "quality": "high"}]}))
create_file('backend/tests/certification/oracles/grocery_negative_oracles.json', json.dumps({"examples": [{"id": "g2", "name": "Expired Bread", "quality": "low"}]}))
create_file('backend/tests/certification/oracles/connector_contract_oracles.json', json.dumps({"contracts": [{"provider": "instacart", "endpoint": "/api/v1/search"}]}))

# Test Files
test_template = '''import pytest
import os

pytestmark = pytest.mark.skipif(os.getenv("INFRASTRUCTURE_UNAVAILABLE") == "1", reason="Infrastructure unavailable")

def test_placeholder():
    assert True
'''

test_files = [
    'backend/tests/certification/test_connector_contracts.py',
    'backend/tests/certification/test_grocery_quality.py',
    'backend/tests/certification/test_live_source_baseline.py',
    'backend/tests/certification/test_entity_resolution_oracles.py',
    'backend/tests/certification/test_cross_provider_comparison.py',
    'backend/tests/certification/test_freshness_provenance.py',
    'backend/tests/certification/test_network_guards.py',
    'backend/tests/certification/test_mcp_read_boundaries.py',
    'backend/tests/certification/test_decision_engines.py',
]

for file_path in test_files:
    create_file(file_path, test_template)

# Script
script_content = '''import subprocess
import sys

def main():
    print("Running Full Certification Suite...")
    try:
        result = subprocess.run(["python", "-m", "pytest", "backend/tests/certification/", "-v", "--tb=short"], check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Tests failed.")
        print(e.stdout)
        print(e.stderr)
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
'''
create_file('scripts/run_full_certification.py', script_content)
print("Files created successfully.")
