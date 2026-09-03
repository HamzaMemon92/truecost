from fastapi import APIRouter, Depends
from app.schemas.grocery import GroceryRequest, GroceryResponse, BasketEvaluationRequest, BasketComparisonResult
from app.graph.grocery_workflow import compile_grocery_workflow
from app.observability.logging import log_event
from app.providers.canonical_catalog import get_canonical_catalog
from app.providers.grocery_registry import get_grocery_providers
from app.providers.grocery_base import normalize_grocery_results

router = APIRouter()
grocery_workflow = compile_grocery_workflow()

@router.post("/query", response_model=GroceryResponse)
async def grocery_query(payload: GroceryRequest) -> GroceryResponse:
    state = {
        "items": payload.items,
        "category": payload.category,
        "session_id": payload.session_id,
        "user_id": payload.user_id,
        "preferences": payload.preferences,
        "reasoning": [],
        "verification": [],
        "substitutions": [],
        "recommended_basket": None,
        "alternative_baskets": [],
        "complexity": "simple",
        "route": "direct-basket",
        "mcp_tools_used": [],
        "mcp_results": [],
        "observability": [],
        "response": {},
    }

    result = await grocery_workflow.ainvoke(state)
    response = GroceryResponse(**result["response"])
    log_event("grocery_query_completed", items=payload.items, complexity=response.complexity, route=response.route)
    return response

@router.post("/basket/evaluate", response_model=list[BasketComparisonResult])
async def evaluate_grocery_basket(payload: BasketEvaluationRequest) -> list[BasketComparisonResult]:
    """Basket evaluation using ingested observations."""
    from app.category_catalog import get_canonical_catalog
    from app.repositories.grocery_observation_repository import grocery_observations, GROCERY_OBSERVATION_PROVIDERS
    from app.services.grocery.basket import BasketBuilder
    from app.services.grocery.cost_engine import CostCalculator
    from app.services.grocery.constraint_engine import ConstraintEngine
    from app.services.grocery.optimizer import BasketOptimizer
    from app.schemas.grocery import BasketComparisonResult, FulfillmentGroup, CanonicalGroceryItem

    catalog = get_canonical_catalog()
    catalog_map = {p.canonical_product_id: p for p in catalog}
    
    available_items = []
    
    # Extract items from observation repository instead of live network calls
    for item in payload.items:
        c_prod = catalog_map.get(item.canonical_product_id)
        if c_prod:
            # Query the observation repository using the catalog title
            observations = grocery_observations.search_observations_as_canonical(
                c_prod.title, 
                GROCERY_OBSERVATION_PROVIDERS
            )
            # Force canonical IDs on matches for the basket builder
            for obs in observations:
                if c_prod.title.lower() in obs["title"].lower():
                    obs["canonical_product_id"] = c_prod.canonical_product_id
                    if c_prod.image_confidence == "TRUSTED":
                        obs["retailer_image_url"] = c_prod.image_url
                        obs["image_verified"] = True
                        obs["image_source"] = "canonical"
                    available_items.append(CanonicalGroceryItem(**obs))
                    
    # Build the basket
    baskets = BasketBuilder.build(available_items, payload.items)
    
    # Calculate costs
    for b in baskets:
        CostCalculator.calculate_all(b, payload.location)
        
    # Apply constraints
    valid_baskets = []
    for b in baskets:
        if ConstraintEngine.evaluate_all(b):
            valid_baskets.append(b)
            
    if not valid_baskets:
        return []
        
    # Rank baskets
    ranked = BasketOptimizer.optimize(valid_baskets, payload.mode)
    
    results = []
    for mode, b_list in ranked.items():
        if b_list:
            best = b_list[0]
            fg = FulfillmentGroup(
                provider=best.provider,
                items=best.items,
                subtotal=best.subtotal,
                delivery_fee=best.delivery_fee,
                platform_fee=best.platform_fee,
                discount=best.discount,
                coupon_discount=best.coupon_discount,
                final_total=best.final_total,
                estimated_delivery=best.estimated_delivery,
                missing_items=best.missing_items,
                deep_link_type="UNAVAILABLE",
                deep_link_url=None
            )
            results.append(BasketComparisonResult(mode=mode, fulfillment_group=fg))
            
    return results






