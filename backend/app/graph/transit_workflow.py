from __future__ import annotations
from typing import TypedDict, Annotated, Any
import operator, re
from langgraph.graph import StateGraph, START, END

class TransitState(TypedDict):
    origin: str
    destination: str
    mode: str  # 'mobility' or 'travel'
    query: str  # raw search query (e.g. "MG Road to Indiranagar")
    options: Annotated[list[Any], operator.add]
    recommendation: dict[str, Any]
    provider_network_calls: int

def parse_route(state: TransitState) -> dict:
    # Extract query from origin/destination if query not set
    query = state.get("query", f"{state['origin']} to {state['destination']}")
    return {"query": query, "provider_network_calls": 0}

def fetch_fares(state: TransitState) -> dict:
    try:
        from app.repositories.search_cache import search_cache
        query = state.get("query", f"{state['origin']} to {state['destination']}")
        results = search_cache.search(state["mode"], query)
        return {"options": results}
    except Exception as e:
        return {"options": [], "recommendation": {"error": str(e)}}

def evaluate_options(state: TransitState) -> dict:
    options = state["options"]
    if not options:
        return {"recommendation": {"status": "no_data", "note": "Ingest provider data first"}}
    
    def price_of(item):
        prices = item.get("prices", [])
        return prices[0].get("price", 9999) if prices else 9999
    
    sorted_options = sorted(options, key=price_of)
    winner = sorted_options[0]
    cheapest_price = price_of(winner)
    most_expensive = price_of(sorted_options[-1])
    saving = most_expensive - cheapest_price
    
    return {
        "options": sorted_options,
        "recommendation": {
            "winner": winner.get("name", "Unknown"),
            "winner_provider": winner.get("brand", ""),
            "price": cheapest_price,
            "saving_vs_most_expensive": saving,
            "all_options_count": len(options),
        }
    }

def compile_transit_workflow():
    workflow = StateGraph(TransitState)
    workflow.add_node("parse_route", parse_route)
    workflow.add_node("fetch_fares", fetch_fares)
    workflow.add_node("evaluate_options", evaluate_options)
    workflow.add_edge(START, "parse_route")
    workflow.add_edge("parse_route", "fetch_fares")
    workflow.add_edge("fetch_fares", "evaluate_options")
    workflow.add_edge("evaluate_options", END)
    return workflow.compile()
