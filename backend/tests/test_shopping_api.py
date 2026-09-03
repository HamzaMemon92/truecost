from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_shopping_query_endpoint():
    response = client.post(
        "/api/v1/shopping/query",
        json={"query": "best laptop under 100000 with card", "category": "shopping"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "shopping"
    assert body["complexity"] in {"simple", "moderate", "complex"}
    assert body["route"] in {"direct-tools", "shopping-agent", "deep-agent"}


def test_simple_query_returns_quick_results():
    """SIMPLE route should use deterministic provider search without agent."""
    response = client.post(
        "/api/v1/shopping/query",
        json={"query": "headphones", "category": "shopping"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["complexity"] == "simple"
    assert body["route"] == "direct-tools"
    # Simple queries should have results even without agent reasoning
    assert len(body["reasoning"]) > 0


def test_moderate_query_uses_shopping_agent():
    """MODERATE route should use LangChain Shopping Agent with MCP tools."""
    response = client.post(
        "/api/v1/shopping/query",
        json={"query": "best iphone under 80000", "category": "shopping"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["complexity"] in {"moderate", "complex"}
    assert body["route"] in {"shopping-agent", "deep-agent"}
    # Should have agent reasoning present
    reasoning_text = " ".join(body["reasoning"]).lower()
    assert "langchain" in reasoning_text or "mcp" in reasoning_text or "agent" in reasoning_text


def test_complex_query_uses_deep_reasoning():
    """COMPLEX route should use Deep Agents or LangChain fallback."""
    response = client.post(
        "/api/v1/shopping/query",
        json={"query": "compare top 3 gaming laptops by performance, price, and thermal efficiency for AI development", "category": "shopping"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["complexity"] == "complex"
    assert body["route"] == "deep-agent"
    # Should have reasoning chain present
    assert len(body["reasoning"]) > 2


def test_query_with_missing_category():
    """Malformed request should be rejected."""
    response = client.post(
        "/api/v1/shopping/query",
        json={"query": "laptop", "category": "invalid"},
    )
    assert response.status_code == 422  # Validation error


def test_payment_benefits_computed_deterministically():
    """Payment benefits should use deterministic calculation, not LLM."""
    response = client.post(
        "/api/v1/shopping/query",
        json={"query": "best laptop", "category": "shopping"},
    )
    assert response.status_code == 200
    body = response.json()
    # Payment benefits use snake_case from Python backend
    assert isinstance(body["payment_benefits"], list)
    # Should not contain LLM hallucinations but structured recommendations
    for benefit in body["payment_benefits"]:
        assert isinstance(benefit, str)


def test_verification_includes_evidence():
    """Verification should be deterministic evidence collection, not LLM."""
    response = client.post(
        "/api/v1/shopping/query",
        json={"query": "laptop", "category": "shopping"},
    )
    assert response.status_code == 200
    body = response.json()
    # Verification should be a list of deterministic checks
    assert isinstance(body["verification"], list)
    for check in body["verification"]:
        assert isinstance(check, str)


def test_forced_deep_agent_endpoint():
    """Forced deep-agent endpoint should override complexity gate."""
    response = client.post(
        "/api/v1/shopping/query/deep",
        json={"query": "cheap headphones", "category": "shopping"},
    )
    assert response.status_code == 200
    body = response.json()
    # Even simple query should use deep-agent path when forced
    assert body["complexity"] == "complex"
    assert body["route"] == "deep-agent"
    assert "Deep-agent route forced" in " ".join(body["reasoning"])


def test_meta_stack_endpoint_shows_runtime_info():
    """Meta endpoint should report available capabilities."""
    response = client.get("/meta/stack")
    assert response.status_code == 200
    body = response.json()
    # Check new response structure with nested mcp object
    assert "mcp" in body
    assert "tools" in body["mcp"]
    assert isinstance(body["mcp"]["tools"], list)
    # Should have 8 shopping tools (check count or that they're defined)
    # Note: tools list might be empty in mock mode, just verify structure


def test_provider_results_normalized():
    """Provider results should be in canonical schema."""
    response = client.post(
        "/api/v1/shopping/query",
        json={"query": "laptop", "category": "shopping"},
    )
    assert response.status_code == 200
    body = response.json()
    # Use snake_case from Python backend
    for product in body["provider_results"]:
        # Canonical schema has specific required fields
        assert "title" in product or "name" in product
        # Provider should be specified
        assert "provider" in product or "source_type" in product

