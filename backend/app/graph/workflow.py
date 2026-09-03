from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.shopping_agent import choose_route, determine_complexity, run_agent_path
from app.graph.state import ShoppingGraphState
from app.mcp.client import ShoppingMcpClient
from app.observability.logging import log_event
from app.providers.base import normalize_provider_results
from app.providers.registry import get_providers
from app.schemas.shopping import CanonicalProduct, ShoppingRequest, ShoppingResponse
from app.services.payment_intelligence import compute_payment_benefits
from app.services.ranking import select_recommendation
from app.services.verification import build_verification_notes


def _validate_request(state: ShoppingGraphState) -> ShoppingGraphState:
    ShoppingRequest(
        query=state["query"],
        category=state["category"],
        session_id=state["session_id"],
        user_id=state["user_id"],
        preferences=state["preferences"],
    )
    state["reasoning"].append("Request validated.")
    return state


def _load_user_context(state: ShoppingGraphState) -> ShoppingGraphState:
    state["context"] = {
        "city": "Bengaluru, India",
        "preferred_delivery": "balanced",
        "session_id": state["session_id"] or "session-local",
    }
    state["reasoning"].append("User context loaded.")
    return state


def _complexity_gate(state: ShoppingGraphState) -> ShoppingGraphState:
    if state.get("force_deep_agent"):
        state["complexity"] = "complex"
        state["route"] = "deep-agent"
        state["reasoning"].append("Deep-agent route forced by endpoint policy.")
        return state

    complexity = determine_complexity(state["query"])
    route = choose_route(complexity)
    state["complexity"] = complexity
    state["route"] = route
    state["reasoning"].append(f"Complexity gate resolved to {complexity} with route {route}.")
    return state


async def _provider_search(state: ShoppingGraphState) -> ShoppingGraphState:
    providers = get_providers()
    products: list[CanonicalProduct] = []
    state.setdefault("provider_warnings", [])
    state.setdefault("reasoning", [])

    for provider in providers:
        try:
            provider_items = await provider.search(state["query"])
        except Exception as exc:
            state["provider_warnings"].append(f"Provider {getattr(provider, 'name', type(provider).__name__)} unavailable: {exc}")
            continue

        if not isinstance(provider_items, list):
            state["provider_warnings"].append(f"Provider {getattr(provider, 'name', type(provider).__name__)} returned malformed data.")
            continue

        try:
            normalized_items = normalize_provider_results(provider, provider_items)
        except Exception:
            state["provider_warnings"].append(
                f"Provider {getattr(provider, 'name', type(provider).__name__)} returned malformed product data; skipped invalid item."
            )
            continue

        products.extend(normalized_items)

    if not products:
        state["provider_warnings"].append("No provider data available.")

    state["provider_results"] = products
    state["reasoning"].append(f"Provider search returned {len(products)} valid items.")
    return state


import json

import json

async def _shopping_agent(state: ShoppingGraphState) -> ShoppingGraphState:
    mcp = ShoppingMcpClient()
    agent_result = await run_agent_path(state["query"], state["route"], mcp)
    
    state["reasoning"].extend(agent_result.get("reasoning", []))
    state["agent_type"] = agent_result.get("agent_type")
    state["mcp_tools_used"] = agent_result.get("mcp_tools_used", [])
    state["mcp_results"] = agent_result.get("mcp_results", [])
    if agent_result.get("evidence"):
        state["evidence"] = [agent_result["evidence"]]
    else:
        state["evidence"] = []
    
    provider_results = []
    for mcp_res in state["mcp_results"]:
        if "result" in mcp_res:
            res = mcp_res["result"]
            texts_to_parse = []
            if isinstance(res, str):
                texts_to_parse.append(res)
            elif isinstance(res, list):
                for item in res:
                    if hasattr(item, "text") and isinstance(item.text, str):
                        texts_to_parse.append(item.text)
            
            for text in texts_to_parse:
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict) and "results" in parsed and isinstance(parsed["results"], list):
                        for prod in parsed["results"]:
                            try:
                                provider_results.append(CanonicalProduct(**prod))
                            except Exception:
                                pass
                except Exception:
                    pass
                    
    state["provider_results"] = provider_results
    return state


def _recommend(state: ShoppingGraphState) -> ShoppingGraphState:
    state["recommendation"] = select_recommendation(state["provider_results"])
    if state["recommendation"] is None:
        state["provider_warnings"].append("No recommendation could be selected.")
    else:
        state["reasoning"].append(f"Recommendation selected: {state['recommendation'].title}.")
    return state


def _payment_intelligence(state: ShoppingGraphState) -> ShoppingGraphState:
    state["payment_benefits"] = compute_payment_benefits(state["query"], state["recommendation"])
    if state["payment_benefits"]:
        state["reasoning"].append("Payment intelligence computed.")
    else:
        state["reasoning"].append("No payment benefits applicable.")
    return state


def _verification(state: ShoppingGraphState) -> ShoppingGraphState:
    state["verification"] = build_verification_notes(
        state["query"], state["recommendation"], len(state["provider_results"])
    )
    state["reasoning"].append("Verification complete.")
    return state


def _response(state: ShoppingGraphState) -> ShoppingGraphState:
    payload = ShoppingResponse(
        query=state["query"],
        complexity=state["complexity"],
        route=state["route"],
        recommendation=state["recommendation"],
        provider_results=state["provider_results"],
        verification=state["verification"],
        payment_benefits=state["payment_benefits"],
        provider_warnings=state["provider_warnings"],
        reasoning=state["reasoning"],
    )
    state["response"] = payload.model_dump(mode="json")
    log_event("shopping_response_built", complexity=state["complexity"], route=state["route"])
    return state


def _route_after_gate(state: ShoppingGraphState) -> str:
    if state["route"] == "direct-tools":
        return "direct_provider_search"
    return "shopping_agent"


def compile_workflow():
    graph = StateGraph(ShoppingGraphState)
    graph.add_node("validate_request", _validate_request)
    graph.add_node("load_user_context", _load_user_context)
    graph.add_node("complexity_gate", _complexity_gate)
    graph.add_node("direct_provider_search", _provider_search)
    graph.add_node("shopping_agent", _shopping_agent)
    graph.add_node("recommend", _recommend)
    graph.add_node("payment_intelligence", _payment_intelligence)
    graph.add_node("verification", _verification)
    graph.add_node("response", _response)

    graph.add_edge(START, "validate_request")
    graph.add_edge("validate_request", "load_user_context")
    graph.add_edge("load_user_context", "complexity_gate")
    graph.add_conditional_edges(
        "complexity_gate",
        _route_after_gate,
        {
            "direct_provider_search": "direct_provider_search",
            "shopping_agent": "shopping_agent",
        },
    )
    graph.add_edge("direct_provider_search", "verification")
    graph.add_edge("shopping_agent", "verification")
    graph.add_edge("verification", "payment_intelligence")
    graph.add_edge("payment_intelligence", "recommend")
    graph.add_edge("recommend", "response")
    graph.add_edge("response", END)

    return graph.compile()
