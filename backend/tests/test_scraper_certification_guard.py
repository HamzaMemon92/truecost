import asyncio
import json
import uuid
import httpx
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, text

from app.graph.grocery_workflow import compile_grocery_workflow
from app.services.cache import cache
from app.api.endpoints.aggregator import IngestPayload, ingest_scraped_data
from app.db import get_db
from fastapi import Response

# --- Network Guard ---
original_request = httpx.AsyncClient.request
async def network_guard_request(self, method, url, *args, **kwargs):
    host = str(url)
    if "blinkit.com" in host or "zepto.com" in host or "swiggy" in host or "bigbasket" in host:
        raise Exception(f"INDEPENDENT NETWORK GUARD BLOCKED CALL TO: {host}")
    return await original_request(self, method, url, *args, **kwargs)

@pytest.mark.asyncio
@pytest.mark.parametrize("fixture_file", [
    "blinkit_grocery_exact_known_product_live.json",
    "zepto_grocery_exact_known_product_live.json",
    "bigbasket_grocery_exact_known_product_live.json"
])
async def test_live_certification(fixture_file):
    engine = create_engine('sqlite:///./decision_advisor.db')
    
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM ingested_provider_results"))
        conn.execute(text("DELETE FROM search_sessions"))
        conn.execute(text("DELETE FROM entity_resolution_records"))
        conn.commit()

    with open(f"tests/fixtures/scraper_certification/runs/TEST_REPLAY_FIXTURE/{fixture_file}", "r", encoding="utf-8-sig") as f:
        capture = json.load(f)
        
    if hasattr(cache, "redis_client"):
        cache.redis_client.flushall()
    elif hasattr(cache, "_store"):
        cache._store.clear()
        
    payload = IngestPayload(
        provider=capture["provider"],
        raw_data=capture["payload"],
        search_session_id=str(uuid.uuid4()),
        query=capture["query"],
        category="Grocery",
        message_type="SEARCH_SUCCESS"
    )
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        await ingest_scraped_data(payload=payload, response=Response(), db=db, credentials=None)
    finally:
        db_gen.close()
        
    with engine.connect() as conn:
        res = conn.execute(text("SELECT v3_decision, candidate_entity FROM entity_resolution_records WHERE v3_decision='EXACT'")).fetchone()
        assert res is not None, "ERROR: No EXACT match found in ER records!"
        candidate = json.loads(res[1])
        assert candidate is not None
            
    httpx.AsyncClient.request = network_guard_request
    
    # 5b. Mock MCP Client to use daemon's memory cache
    import app.mcp.grocery_client
    from app.repositories.grocery_observation_repository import grocery_observations
    
    async def mock_call_tool(self, tool_name, args):
        if tool_name == "search_items":
            query = args["query"]
            all_items = grocery_observations.search_observations_as_canonical(query, ["blinkit", "zepto", "swiggy", "bigbasket"])
            return {"items": all_items}
        return {}
        
    app.mcp.grocery_client.GroceryMcpClient.call_tool = mock_call_tool
    
    # 6. Run Grocery Workflow
    grocery_workflow = compile_grocery_workflow()
    state = {
        "items": [capture["query"]],
        "category": "grocery",
        "session_id": "test_guard_session",
        "user_id": "test_user",
        "preferences": {},
        "reasoning": [],
        "route": "direct-basket",
        "mcp_tools_used": [],
        "verification": [],
        "substitutions": []
    }
    
    result = await grocery_workflow.ainvoke(state)
    
    basket = result.get("recommended_basket")
    assert basket is not None
    assert len(basket.items) > 0
    assert basket.items[0].er_decision == "EXACT"
