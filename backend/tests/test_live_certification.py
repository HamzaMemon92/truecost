import json
import os
import pytest
from pathlib import Path
from app.providers.grocery_registry import get_grocery_providers
from app.providers.registry import get_providers as get_shopping_providers
from app.schemas.grocery import Location
from app.tools.invariant_evaluator import InvariantEvaluator

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "live_provider_certification_cases.json"

def load_cases():
    if not FIXTURE_PATH.exists():
        return []
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

CASES = load_cases()
GROCERY_PROVIDERS = get_grocery_providers()
SHOPPING_PROVIDERS = get_shopping_providers()

def get_all_provider_pairs():
    pairs = []
    for p in GROCERY_PROVIDERS:
        if "Mock" not in p.__class__.__name__:
            pairs.append((p, "grocery"))
    for p in SHOPPING_PROVIDERS:
        if "Mock" not in p.__class__.__name__:
            pairs.append((p, "shopping"))
    return pairs

@pytest.mark.live_provider
@pytest.mark.asyncio
@pytest.mark.parametrize("provider_tuple", get_all_provider_pairs(), ids=lambda p: p[0].__class__.__name__)
@pytest.mark.parametrize("case", CASES, ids=lambda c: c["test_case_id"])
async def test_live_certification_scenario(provider_tuple, case):
    provider, domain = provider_tuple
    
    if domain not in case.get("domains", []):
        pytest.skip(f"Case {case['test_case_id']} not applicable to domain {domain}")

    if not provider.is_enabled():
        pytest.skip(f"Provider {provider.__class__.__name__} is not enabled (missing credentials?)")

    query = case.get("query", "milk")
    location_strategy = case.get("location_strategy", "valid_explicit")
    
    location = None
    if location_strategy == "valid_explicit":
        lat = os.environ.get("TRUECOST_CERT_LOCATION_1_LAT")
        lon = os.environ.get("TRUECOST_CERT_LOCATION_1_LON")
        if not lat or not lon:
            pytest.skip("Missing TRUECOST_CERT_LOCATION_1 env vars")
        location = Location(latitude=float(lat), longitude=float(lon))
    elif location_strategy == "alternate_valid":
        lat = os.environ.get("TRUECOST_CERT_LOCATION_2_LAT")
        lon = os.environ.get("TRUECOST_CERT_LOCATION_2_LON")
        if not lat or not lon:
            pytest.skip("Missing TRUECOST_CERT_LOCATION_2 env vars")
        location = Location(latitude=float(lat), longitude=float(lon))
    elif location_strategy == "missing":
        location = None
        
    if case.get("simulate_401"):
        pytest.skip("Auth failure simulation handled manually or in CLI tool")

    if case.get("simulate_timeout"):
        pytest.skip("Timeout simulation handled manually or in CLI tool")

    results = await provider.search(query, location=location)

    invariants = case.get("expected_invariants", [])
    evaluations = await InvariantEvaluator.evaluate(
        results=results, 
        invariants=invariants, 
        provider_name=provider.__class__.__name__, 
        query=query, 
        test_config=case.get("entity_test_config"),
        observability=None
    )
    
    failures = [ev for ev in evaluations if ev["status"] == "FAIL"]
    if failures:
        pytest.fail(f"Invariants failed: {failures}")
