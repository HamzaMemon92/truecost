from __future__ import annotations
from typing import TypedDict, Annotated, Any
import operator
from langgraph.graph import StateGraph, START, END

class EvaluationState(TypedDict):
    requirements: str
    domain: str  # 'finance', 'productivity'
    query: str
    candidates: Annotated[list[Any], operator.add]
    comparison_matrix: dict[str, Any]
    provider_network_calls: int

def extract_requirements(state: EvaluationState) -> dict:
    return {"query": state.get("requirements", ""), "provider_network_calls": 0}

def gather_candidates(state: EvaluationState) -> dict:
    try:
        from app.repositories.search_cache import search_cache
        query = state.get("query", state.get("requirements", ""))
        results = search_cache.search(state["domain"], query)
        return {"candidates": results}
    except Exception as e:
        return {"candidates": [], "comparison_matrix": {"error": str(e)}}

def build_comparison(state: EvaluationState) -> dict:
    candidates = state["candidates"]
    if not candidates:
        return {"comparison_matrix": {"status": "no_data", "note": "Ingest provider data first"}}
    
    # Build comparison by provider
    by_provider = {}
    for c in candidates:
        provider = c.get("brand", c.get("provider", "unknown"))
        prices = c.get("prices", [])
        price = prices[0].get("price", None) if prices else None
        by_provider[provider] = {
            "name": c.get("name", ""),
            "price": price,
            "features": c.get("weight_volume", ""),
        }
    
    # Find best value
    priced = {k: v for k, v in by_provider.items() if v["price"] is not None}
    best = min(priced.items(), key=lambda x: x[1]["price"]) if priced else None
    
    return {
        "comparison_matrix": {
            "by_provider": by_provider,
            "best_value": best[0] if best else None,
            "best_price": best[1]["price"] if best else None,
            "providers_compared": len(by_provider),
        }
    }

def compile_evaluation_workflow():
    workflow = StateGraph(EvaluationState)
    workflow.add_node("extract_requirements", extract_requirements)
    workflow.add_node("gather_candidates", gather_candidates)
    workflow.add_node("build_comparison", build_comparison)
    workflow.add_edge(START, "extract_requirements")
    workflow.add_edge("extract_requirements", "gather_candidates")
    workflow.add_edge("gather_candidates", "build_comparison")
    workflow.add_edge("build_comparison", END)
    return workflow.compile()
