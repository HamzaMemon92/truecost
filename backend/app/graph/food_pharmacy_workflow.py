from __future__ import annotations
from typing import TypedDict, Annotated, Any
import operator
from langgraph.graph import StateGraph, START, END
from app.connectors.zomato import ZomatoConnector
from app.connectors.swiggy_food import SwiggyFoodConnector
from app.connectors.tata1mg import Tata1mgConnector
from app.connectors.pharmeasy import PharmEasyConnector

class FoodPharmacyState(TypedDict):
    query: str
    category: str  # 'food' or 'pharmacy'
    items: Annotated[list[Any], operator.add]
    ranked_options: list[Any]
    errors: list[str]
    provider_network_calls: int

# The key: connectors parse whatever cached payload exists. For now, they operate
# on data that was already ingested via POST /api/v1/aggregator/ingest.
# The workflow's job is to rank what's been ingested — NOT to fetch live.

def extract_intent(state: FoodPharmacyState) -> dict:
    return {"errors": [], "provider_network_calls": 0}

def search_providers(state: FoodPharmacyState) -> dict:
    # Read from in-memory search cache (written by the aggregator on ingest)
    try:
        from app.repositories.search_cache import search_cache
        results = search_cache.search(state["category"], state["query"])
        return {"items": results}
    except Exception as e:
        return {"items": [], "errors": [str(e)]}

def normalize_results(state: FoodPharmacyState) -> dict:
    # Deduplicate by name (case-insensitive)
    seen = set()
    unique = []
    for item in state["items"]:
        key = str(item.get("name", "")).lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return {"items": unique}

def rank_options(state: FoodPharmacyState) -> dict:
    # Rank by price ascending, then by eta ascending
    items = state["items"]
    def sort_key(item):
        prices = item.get("prices", [])
        price = prices[0].get("price", 9999) if prices else 9999
        eta = prices[0].get("delivery_time", "") if prices else ""
        # Parse eta minutes from string like "30 mins"
        import re
        m = re.search(r'(\d+)', str(eta))
        eta_mins = int(m.group(1)) if m else 999
        return (price, eta_mins)
    ranked = sorted(items, key=sort_key)
    # Mark cheapest
    if ranked:
        ranked[0]["is_best_price"] = True
    return {"ranked_options": ranked}

def compile_food_pharmacy_workflow():
    workflow = StateGraph(FoodPharmacyState)
    workflow.add_node("extract_intent", extract_intent)
    workflow.add_node("search_providers", search_providers)
    workflow.add_node("normalize_results", normalize_results)
    workflow.add_node("rank_options", rank_options)
    workflow.add_edge(START, "extract_intent")
    workflow.add_edge("extract_intent", "search_providers")
    workflow.add_edge("search_providers", "normalize_results")
    workflow.add_edge("normalize_results", "rank_options")
    workflow.add_edge("rank_options", END)
    return workflow.compile()
