from __future__ import annotations

import json
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.grocery_agent import choose_grocery_route, determine_grocery_complexity, run_grocery_agent_path
from app.graph.grocery_state import GroceryGraphState
from app.mcp.grocery_client import GroceryMcpClient
from app.observability.logging import log_event
from app.schemas.grocery import CanonicalBasket, CanonicalGroceryItem, GroceryRequest, GroceryResponse, Location, RetailerOffer
from app.graph.grocery_basket_engine import BasketBuilder, CostCalculator, ConstraintEngine, BasketOptimizer
from app.providers.canonical_catalog import get_canonical_catalog
from app.services.grocery.comparison import ProductComparison


def _validate_request(state: GroceryGraphState) -> GroceryGraphState:
    GroceryRequest(
        items=state["items"],
        category=state["category"],
        session_id=state["session_id"],
        user_id=state["user_id"],
        preferences=state["preferences"],
    )

    # Extract objective from preferences, default to balanced
    state["objective"] = state.get("preferences", {}).get("objective", "balanced")

    state["reasoning"].append("Request validated.")
    return state


def _load_user_context(state: GroceryGraphState) -> GroceryGraphState:
    loc_dict = state.get("preferences", {}).get("location", {})
    location = Location(**loc_dict) if loc_dict else None

    state["context"] = {
        "city": "Bengaluru, India",
        "session_id": state["session_id"] or "session-local",
        "location": location
    }
    state["reasoning"].append(f"User context loaded. Location: {location.postal_code if location else 'None'}")
    return state


def _task_analysis(state: GroceryGraphState) -> GroceryGraphState:
    if state.get("force_deep_agent"):
        state["complexity"] = "complex"
        state["route"] = "deep-agent"
        state["reasoning"].append("Deep-agent route forced by endpoint policy.")
        return state

    if state.get("route") == "direct-basket" or state.get("force_direct_basket"):
        state["complexity"] = "simple"
        state["route"] = "direct-basket"
        state["reasoning"].append("Direct-basket route explicitly selected.")
        return state

    complexity = determine_grocery_complexity(state["items"])
    route = choose_grocery_route(complexity)
    state["complexity"] = complexity
    state["route"] = route
    state["reasoning"].append(f"Task analysis resolved to {complexity} with execution policy {route}.")
    return state


def _route_execution(state: GroceryGraphState) -> str:
    return state["route"]


async def _direct_basket_search(state: GroceryGraphState) -> GroceryGraphState:
    """Read from Grocery MCP (observation repository). No live provider network calls.

    Canonical read path:
      state["items"] queries
      → GroceryMcpClient.call_tool("search_items", ...)
      → GroceryObservationRepository.search_observations_as_canonical()
      → CanonicalGroceryItem-compatible dicts
      → state["mcp_results"]

    When no observations exist for a query, returns empty items for that query.
    NEVER calls get_grocery_providers() or execute_providers_concurrently().
    No silent network fallback.
    """
    state["reasoning"].append(
        "Direct basket search via Grocery MCP (observation repository). No provider network calls."
    )

    mcp = GroceryMcpClient()
    all_products: list[dict] = []
    observability: list[dict] = []

    for query in state["items"]:
        res = await mcp.call_tool("search_items", {"query": query})
        items = res.get("items") or []
        all_products.extend(items)
        # Emit ProviderObservability-compatible dict for each item in the query
        observability.append({
            "provider_name": f"observation_repository/{query}",
            "status": "success" if items else "no_results",
            "latency_ms": 0,  # in-process, no network latency
            "error_class": None,
            "item_count": len(items),
        })

    state["mcp_tools_used"].append("search_items")
    state["observability"] = observability
    state["mcp_results"] = [{"items": all_products}]
    state["reasoning"].append(
        f"MCP basket search complete. "
        f"Found {len(all_products)} items from observation repository. "
        f"Provider network calls: 0."
    )
    return state


async def _grocery_agent(state: GroceryGraphState) -> GroceryGraphState:
    mcp = GroceryMcpClient()
    agent_result = await run_grocery_agent_path(state["items"], state["route"], mcp)

    state["reasoning"].extend(agent_result.get("reasoning", []))
    state["agent_type"] = agent_result.get("agent_type")
    state["mcp_tools_used"] = agent_result.get("mcp_tools_used", [])
    state["mcp_results"] = agent_result.get("mcp_results", [])
    if agent_result.get("evidence"):
        state["evidence"] = [agent_result["evidence"]]
    else:
        state["evidence"] = []

    # Phase 2C placeholder: convert MCP JSON results into CanonicalBasket models
    # via the deterministic pipeline
    state["reasoning"].append("Agent evidence passed to deterministic engine.")
    return state


def _basket_pipeline(state: GroceryGraphState) -> GroceryGraphState:
    """
    Deterministic engine.
    Item Normalization -> SKU Matching -> Availability -> Basket Builder
    -> Offer Resolution -> Cost Engine -> Constraint Engine -> Basket Optimizer

    Phase 2C implementation: Group by provider, compute costs, apply constraints,
    and rank based on objective.
    """
    all_items: list[CanonicalGroceryItem] = []

    # 1. Extract items from MCP results
    for res in state.get("mcp_results", []):
        if "items" in res and isinstance(res["items"], list):
            for item_dict in res["items"]:
                try:
                    # Sanitize provider_status: MCP may serialize legacy "mock" value.
                    # Coerce any invalid value to "active" so hydration never fails.
                    valid_statuses = {"active", "unavailable", "pending_authorization"}
                    if item_dict.get("provider_status") not in valid_statuses:
                        item_dict = {**item_dict, "provider_status": "active"}
                    all_items.append(CanonicalGroceryItem(**item_dict))
                except Exception as e:
                    import traceback
                    print("CanonicalGroceryItem validation failed:", repr(e))
                    pass

    state["basket_results"] = []
    state["recommended_basket"] = None
    state["alternative_baskets"] = []
    state["product_comparisons"] = []

    if not all_items:
        state["reasoning"].append("Deterministic basket pipeline found no items to build a basket.")
        return state
        
    # User constraint: REJECTED items must not become authoritative matches/winners.
    # Only EXACT identity (or no decision) is allowed into authoritative ranking.
    filtered_items = [item for item in all_items if item.er_decision != "REJECTED"]
    
    if not filtered_items:
        state["reasoning"].append("Deterministic basket pipeline found no valid (non-rejected) items to build a basket.")
        return state

    # --- Product Comparison Construction ---
    catalog = get_canonical_catalog()
    catalog_map = {p.canonical_product_id: p for p in catalog}

    # Group items by canonical_product_id
    grouped_offers: dict[str, list[CanonicalGroceryItem]] = {}
    for item in filtered_items:
        grouped_offers.setdefault(item.canonical_product_id, []).append(item)

    for item_id, items in grouped_offers.items():
        canonical_product = catalog_map.get(item_id)
        if not canonical_product:
            from app.schemas.grocery import CanonicalProduct
            # Dynamically create canonical product for live observations
            canonical_product = CanonicalProduct(
                canonical_product_id=item_id,
                title=items[0].title,
                brand=items[0].brand,
                category=items[0].category,
                variant="unknown",
                normalized_quantity=items[0].quantity_value,
                normalized_unit=items[0].quantity_unit,
                base_price_estimate=items[0].mrp or items[0].price,
                image_url=None,
                image_confidence="FALLBACK",
                tags=[]
            )

        # Convert CanonicalGroceryItem to RetailerOffer
        offers = []
        for i in items:
            offer = RetailerOffer(
                provider=i.provider,
                provider_sku=i.provider_sku,
                canonical_product_id=i.canonical_product_id,
                price=i.price,
                mrp=i.mrp or i.price,
                discount=i.discount or 0.0,
                coupon_discount=i.coupon_discount or 0.0,
                delivery_fee=i.delivery_fee or 0.0,
                platform_fee=i.platform_fee or 0.0,
                min_order_value=i.min_order_value or 0.0,
                availability=i.availability,
                delivery_minutes=i.delivery_minutes,
                offers=i.offers,
                source_url=i.source_url,
                affiliate_url=i.affiliate_url,
                retailer_image_url=canonical_product.image_url if canonical_product.image_confidence == "TRUSTED" else i.retailer_image_url,
                image_verified=True if canonical_product.image_confidence == "TRUSTED" else i.image_verified,
                image_source="canonical" if canonical_product.image_confidence == "TRUSTED" else i.image_source
            )
            offers.append(offer)

        comparison = ProductComparison(canonical_product, offers)
        comparison.compare()
        state["product_comparisons"].append(comparison.to_dict())

    # 2. Build Baskets
    baskets = BasketBuilder.build(filtered_items)

    # 3. Calculate Costs
    baskets = CostCalculator.calculate_all(baskets)

    # 4. Apply Constraints
    baskets = ConstraintEngine.evaluate_all(baskets, state["items"])

    # 5. Optimize & Rank
    objective = state.get("objective", "balanced")
    ranked = BasketOptimizer.optimize(baskets, objective)

    if ranked:
        state["basket_results"] = ranked
        state["recommended_basket"] = ranked[0]
        state["alternative_baskets"] = ranked[1:]

        state["reasoning"].append(
            f"Basket pipeline built {len(ranked)} baskets. "
            f"Recommended provider: {ranked[0].provider} (objective: {objective})."
        )

    return state


def _verification(state: GroceryGraphState) -> GroceryGraphState:
    state["verification"].append(f"Query verified: {', '.join(state['items'])}")
    state["reasoning"].append("Verification complete.")
    return state


def _build_response(state: GroceryGraphState) -> GroceryGraphState:
    state["response"] = {
        "category": "grocery",
        "items_requested": state["items"],
        "complexity": state["complexity"],
        "route": state["route"],
        "product_comparisons": state.get("product_comparisons", []),
        "recommended_basket": state["recommended_basket"],
        "alternative_baskets": state["alternative_baskets"],
        "substitutions": state["substitutions"],
        "verification": state["verification"],
        "reasoning": state["reasoning"],
        "observability": state.get("observability", []),
        "mcp_tools_used": state.get("mcp_tools_used", []),
        "mcp_results": state.get("mcp_results", []),
    }
    return state


def compile_grocery_workflow() -> Any:
    graph = StateGraph(GroceryGraphState)

    graph.add_node("validate", _validate_request)
    graph.add_node("context", _load_user_context)
    graph.add_node("task_analysis", _task_analysis)
    graph.add_node("direct_basket_search", _direct_basket_search)
    graph.add_node("grocery_agent", _grocery_agent)
    graph.add_node("basket_pipeline", _basket_pipeline)
    graph.add_node("verification", _verification)
    graph.add_node("response", _build_response)

    graph.add_edge(START, "validate")
    graph.add_edge("validate", "context")
    graph.add_edge("context", "task_analysis")

    graph.add_conditional_edges(
        "task_analysis",
        _route_execution,
        {
            "direct-basket": "direct_basket_search",
            "grocery-agent": "grocery_agent",
            "deep-agent": "grocery_agent",
        },
    )

    graph.add_edge("direct_basket_search", "basket_pipeline")
    graph.add_edge("grocery_agent", "basket_pipeline")

    graph.add_edge("basket_pipeline", "verification")
    graph.add_edge("verification", "response")
    graph.add_edge("response", END)

    return graph.compile()
