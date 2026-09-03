import pytest
from app.tools.invariant_evaluator import InvariantEvaluator

class DummyItem:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
            
class DummyDecision:
    def __init__(self, val):
        self.value = val

@pytest.mark.asyncio
async def test_invariant_results_exist_fails_empty():
    evals = await InvariantEvaluator.evaluate([], ["results_exist"], "Mock", "q")
    assert evals[0]["status"] == "FAIL"
    assert "Expected >= 1" in evals[0]["evidence"]["error"]

@pytest.mark.asyncio
async def test_invariant_multiple_results_fails_one():
    mock_item = DummyItem(price=10, source_type="live")
    evals = await InvariantEvaluator.evaluate([mock_item], ["multiple_results"], "Mock", "q")
    assert evals[0]["status"] == "FAIL"

@pytest.mark.asyncio
async def test_invariant_price_required_fails_all_null():
    mock_item = DummyItem(price=None, source_type="live")
    evals = await InvariantEvaluator.evaluate([mock_item], ["price_required"], "Mock", "q")
    assert evals[0]["status"] == "FAIL"
    assert "No valid prices" in evals[0]["evidence"]["error"]

@pytest.mark.asyncio
async def test_invariant_price_valid_fails_negative():
    mock_item = DummyItem(price=-10, source_type="live")
    evals = await InvariantEvaluator.evaluate([mock_item], ["price_valid"], "Mock", "q")
    assert evals[0]["status"] == "FAIL"

@pytest.mark.asyncio
async def test_invariant_live_provenance_fails_mock():
    mock_item = DummyItem(price=10, source_type="mock")
    evals = await InvariantEvaluator.evaluate([mock_item], ["live_provenance"], "Mock", "q")
    assert evals[0]["status"] == "FAIL"
    assert "CRITICAL FAIL" in evals[0]["evidence"]["error"]

@pytest.mark.asyncio
async def test_invariant_live_provenance_fails_staging():
    mock_item = DummyItem(price=10, source_type="staging")
    evals = await InvariantEvaluator.evaluate([mock_item], ["live_provenance"], "Mock", "q")
    assert evals[0]["status"] == "FAIL"

@pytest.mark.asyncio
async def test_invariant_live_provenance_fails_none():
    mock_item = DummyItem(price=10, source_type=None)
    evals = await InvariantEvaluator.evaluate([mock_item], ["live_provenance"], "Mock", "q")
    assert evals[0]["status"] == "FAIL"

@pytest.mark.asyncio
async def test_invariant_deeplink_valid_fails_missing():
    mock_item = DummyItem(price=10, source_type="live") # No URL
    evals = await InvariantEvaluator.evaluate([mock_item], ["deeplink_valid"], "Mock", "q")
    assert evals[0]["status"] == "FAIL"
    assert "No deeplink found" in evals[0]["evidence"]["error"]

@pytest.mark.asyncio
async def test_invariant_deeplink_valid_fails_bad_url():
    mock_item = DummyItem(price=10, source_type="live", url="not_a_url")
    evals = await InvariantEvaluator.evaluate([mock_item], ["deeplink_valid"], "Mock", "q")
    assert evals[0]["status"] == "FAIL"
    assert "Invalid link format" in evals[0]["evidence"]["error"]

@pytest.mark.asyncio
async def test_unknown_invariant_fails_configuration():
    evals = await InvariantEvaluator.evaluate([], ["some_fake_invariant"], "Mock", "q")
    assert evals[0]["status"] == "FAIL"
    assert "Unknown invariant" in evals[0]["evidence"]["error"]

@pytest.mark.asyncio
async def test_false_exact_merge_fails_on_exact(monkeypatch):
    from app.services.entity_resolution import EntityResolutionService
    from app.services.entity_resolution import SourceRecord, TrueCostProduct
    
    # Mock engine to return EXACT
    class MockRes:
        decision = DummyDecision("EXACT")
    
    def mock_resolve(*args, **kwargs):
        return MockRes()
        
    monkeypatch.setattr(EntityResolutionService, "resolve", mock_resolve)
    
    results = [DummyItem(), DummyItem()]
    config = {"candidate_a_index": 0, "candidate_b_index": 1}
    evals = await InvariantEvaluator.evaluate(results, ["no_false_exact_merge"], "Mock", "q", config)
    
    assert evals[0]["status"] == "FAIL"
    assert evals[0]["evidence"]["error"] == "FALSE_EXACT_MERGE"

@pytest.mark.asyncio
async def test_false_exact_merge_fails_on_exception(monkeypatch):
    from app.services.entity_resolution import EntityResolutionService
    def mock_resolve(*args, **kwargs):
        raise ValueError("Boom")
    monkeypatch.setattr(EntityResolutionService, "resolve", mock_resolve)
    
    results = [DummyItem(), DummyItem()]
    config = {"candidate_a_index": 0, "candidate_b_index": 1}
    evals = await InvariantEvaluator.evaluate(results, ["no_false_exact_merge"], "Mock", "q", config)
    
    assert evals[0]["status"] == "FAIL"
    assert "Entity Resolution threw exception" in evals[0]["evidence"]["error"]

@pytest.mark.asyncio
async def test_false_exact_merge_insufficient_evidence():
    results = [DummyItem()] # Only 1 result
    config = {"candidate_a_index": 0, "candidate_b_index": 1}
    evals = await InvariantEvaluator.evaluate(results, ["no_false_exact_merge"], "Mock", "q", config)
    
    assert evals[0]["status"] == "SKIP"
    assert evals[0]["evidence"]["reason"] == "INSUFFICIENT_EVIDENCE"



@pytest.mark.asyncio
async def test_error_mapping_401():
    from app.tools.provider_live_certification import run_certification_for_provider
    class FakeProvider:
        def is_enabled(self): return True
        async def search(self, *args, **kwargs): raise Exception("HTTP 401 Unauthorized")
    
    cases = [{"test_case_id": "c1", "domains": ["grocery"], "severity": "CRITICAL", "query": "q", "location_strategy": "none"}]
    report = await run_certification_for_provider(FakeProvider(), cases, "grocery")
    assert report["case_details"][0]["error"] == "AUTH_FAILURE"

@pytest.mark.asyncio
async def test_error_mapping_402():
    from app.tools.provider_live_certification import run_certification_for_provider
    class FakeProvider:
        def is_enabled(self): return True
        async def search(self, *args, **kwargs): raise Exception("HTTP 402 Payment Required")
    
    cases = [{"test_case_id": "c1", "domains": ["grocery"], "severity": "CRITICAL", "query": "q", "location_strategy": "none"}]
    report = await run_certification_for_provider(FakeProvider(), cases, "grocery")
    assert report["case_details"][0]["error"] == "CREDITS_EXHAUSTED"

@pytest.mark.asyncio
async def test_error_mapping_429():
    from app.tools.provider_live_certification import run_certification_for_provider
    class FakeProvider:
        def is_enabled(self): return True
        async def search(self, *args, **kwargs): raise Exception("HTTP 429 Too Many Requests")
    
    cases = [{"test_case_id": "c1", "domains": ["grocery"], "severity": "CRITICAL", "query": "q", "location_strategy": "none"}]
    report = await run_certification_for_provider(FakeProvider(), cases, "grocery")
    assert report["case_details"][0]["error"] == "RATE_LIMITED"

@pytest.mark.asyncio
async def test_percentile_calculation():
    from app.tools.provider_live_certification import run_certification_for_provider
    class FakeProvider:
        def is_enabled(self): return True
        async def search(self, *args, **kwargs): 
            return [] # Returns empty, but we'll manually patch latencies if needed
            
    # For now, just test that p50/p95 don't crash
    cases = [{"test_case_id": "c1", "domains": ["grocery"], "severity": "OPTIONAL", "query": "q", "location_strategy": "none"}]
    report = await run_certification_for_provider(FakeProvider(), cases, "grocery")
    assert "latency_p50_ms" in report
    assert "latency_p95_ms" in report

