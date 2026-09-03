import pytest
from app.schemas.grocery import GroceryRequest, GroceryResponse, CanonicalBasket
from app.agents.grocery_agent import determine_grocery_complexity, choose_grocery_route, run_grocery_agent_path
from app.mcp.grocery_client import GroceryMcpClient
from app.graph.grocery_workflow import compile_grocery_workflow

@pytest.mark.asyncio
async def test_grocery_schema_validation():
    req = GroceryRequest(
        items=["milk", "eggs"],
        preferences={"objective": "fastest"}
    )
    assert req.items == ["milk", "eggs"]
    assert req.category == "grocery"
    assert req.preferences["objective"] == "fastest"

@pytest.mark.asyncio
async def test_grocery_route_selection():
    # Test temporary complexity heuristics
    assert determine_grocery_complexity(["milk"]) == "simple"
    assert determine_grocery_complexity(["milk", "eggs", "bread"]) == "moderate"
    assert determine_grocery_complexity(["item"] * 12) == "complex"
    
    # Test routing logic
    assert choose_grocery_route("simple") == "direct-basket"
    assert choose_grocery_route("moderate") == "grocery-agent"
    assert choose_grocery_route("complex") == "deep-agent"

@pytest.mark.asyncio
async def test_grocery_mcp_discovery():
    mcp = GroceryMcpClient()
    tools = await mcp.list_tools()
    
    # Should have exactly 6 tools in Phase 2A
    assert len(tools) == 6
    assert "search_items" in tools
    assert "get_availability" in tools
    assert "get_delivery_estimate" in tools

@pytest.mark.asyncio
async def test_grocery_agent_tool_loop(monkeypatch):
    # If the model is unconfigured, we just get fallback logic, but we can verify the contract
    mcp = GroceryMcpClient()
    
    async def fake_invoke_agent(items, mcp, available_tools):
        await mcp.call_tool("search_items", {"query": "milk"})
        return "I found milk."
        
    monkeypatch.setattr("app.agents.grocery_agent._invoke_langchain_agent", fake_invoke_agent)
    
    # Force moderate route for LangChain agent
    result = await run_grocery_agent_path(["milk", "eggs"], "grocery-agent", mcp)
    
    assert "agent_type" in result
    assert "mcp_tools_used" in result
    assert "mcp_results" in result
    assert "evidence" in result
    assert "reasoning" in result

@pytest.mark.asyncio
async def test_grocery_workflow_routing():
    workflow = compile_grocery_workflow()
    
    state = {
        "items": ["milk"], # 1 item -> simple -> direct-basket
        "category": "grocery",
        "session_id": "test",
        "user_id": "test",
        "preferences": {"objective": "cheapest"},
        "force_deep_agent": False,
        "context": {},
        "complexity": "simple",
        "route": "direct-basket",
        "agent_type": None,
        "mcp_tools_used": [],
        "mcp_results": [],
        "evidence": [],
        "basket_results": [],
        "recommended_basket": None,
        "alternative_baskets": [],
        "substitutions": [],
        "verification": [],
        "reasoning": [],
        "response": {},
    }
    
    res = await workflow.ainvoke(state)
    assert res["complexity"] == "simple"
    assert res["route"] == "direct-basket"
    assert res["objective"] == "cheapest"
    
    # Should have populated response
    assert "response" in res
    assert res["response"]["complexity"] == "simple"
