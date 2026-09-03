import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

class MockGoldenProvider:
    name = "GoldenProvider"
    status = "mock"

    async def search(self, query: str):
        return [{
            "provider": "GoldenProvider",
            "provider_product_id": "TEST-999",
            "title": "TEST_GOLDEN_PRODUCT",
            "brand": "GoldenBrand",
            "category": "Electronics",
            "variant": "Base",
            "price": 42999,
            "currency": "INR",
            "availability": "In stock",
            "seller": "Golden Seller",
            "rating": 4.9,
            "review_count": 999,
            "delivery": "1 day",
            "source_type": "mock",
            "confidence": 0.99,
        }]

def test_mcp_golden_path_end_to_end(monkeypatch):
    """
    Prove the full golden path:
    LangGraph -> Shopping Agent -> LangChain Agent -> MCP Tool -> MCP Server -> Provider Adapter -> Provider -> State -> Recommendation -> Response
    """
    # 1. Override the provider registry to return our test provider.
    monkeypatch.setattr("app.providers.registry.get_providers", lambda: [MockGoldenProvider()])

    # 2. Simulate the LLM choosing to use the MCP tool for the search.
    # We mock _invoke_langchain_agent so we don't need a real OpenAI key for this test.
    async def fake_invoke_agent(query, mcp, available_tools):
        await mcp.call_tool("search_products", {"query": query})
        return "Based on the MCP search, I recommend the TEST_GOLDEN_PRODUCT."

    monkeypatch.setattr("app.agents.shopping_agent._invoke_langchain_agent", fake_invoke_agent)

    # 3. Hit the endpoint
    response = client.post(
        "/api/v1/shopping/query",
        json={"query": "best golden product under 100000", "category": "shopping"}
    )
    
    # 4. Assert the response
    assert response.status_code == 200, response.text
    body = response.json()
    
    assert body["route"] == "shopping-agent"
    
    # The provider results must contain our exact test product, proven to come through MCP
    provider_results = body.get("provider_results", [])
    print("BODY DUMP:", body)
    assert any(p["title"] == "TEST_GOLDEN_PRODUCT" for p in provider_results)
    
    # The final recommendation MUST be derived from the provider result, which came through MCP
    recommendation = body.get("recommendation")
    assert recommendation is not None
    assert recommendation["title"] == "TEST_GOLDEN_PRODUCT"
    assert recommendation["price"] == 42999.0
    assert recommendation["provider"] == "GoldenProvider"
