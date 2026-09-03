from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.graph.workflow import compile_workflow
from app.graph.grocery_workflow import compile_grocery_workflow
from app.mcp.client import ShoppingMcpClient
from app.observability.logging import log_event
from app.api.endpoints import auth, commerce, profiles, travel, mobility, preferences, location, deals, support, provider_connections, providers, health, admin, aggregator
from app.schemas.shopping import HealthResponse, ShoppingRequest, ShoppingResponse
from app.schemas.grocery import GroceryRequest, GroceryResponse
from app.config import settings

app = FastAPI(title="Decision Advisor Backend", version="0.1.0")

def _csv(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def _dev_trusted_hosts() -> list[str]:
    if settings.app_env.lower() in {"development", "test"}:
        return ["*"]
    hosts = set(_csv(settings.trusted_hosts) or ["localhost", "127.0.0.1"])
    hosts.discard("*")
    return sorted(hosts)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    return response


def _error_response(request: Request, status_code: int, code: str, message: str, details=None) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID") or str(uuid4())
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
                **({"details": jsonable_encoder(details)} if details is not None else {}),
            }
        },
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("detail") or "Request failed")
        code = str(detail.get("code") or f"HTTP_{exc.status_code}")
        details = detail.get("details")
    else:
        message = str(detail)
        code = f"HTTP_{exc.status_code}"
        details = None
    return _error_response(request, exc.status_code, code, message, details)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(request, 422, "VALIDATION_ERROR", "Request validation failed", exc.errors())


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log_event("api_unhandled_exception", path=str(request.url.path), error_type=type(exc).__name__)
    return _error_response(request, 500, "INTERNAL_SERVER_ERROR", "Internal server error")


app.add_middleware(TrustedHostMiddleware, allowed_hosts=_dev_trusted_hosts())

app.add_middleware(
    CORSMiddleware,
    allow_origins=_csv(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["profiles"])
app.include_router(preferences.router, prefix="/api/v1/preferences", tags=["preferences"])
app.include_router(location.router, prefix="/api/v1/location", tags=["location"])
app.include_router(provider_connections.router, prefix="/api/v1/provider-connections", tags=["provider connections"])
app.include_router(commerce.router, prefix="/api/v1/commerce", tags=["commerce"])
app.include_router(travel.router, prefix="/api/v1/travel", tags=["travel"])
app.include_router(mobility.router, prefix="/api/v1/mobility", tags=["mobility"])
app.include_router(deals.router, prefix="/api/v1/deals", tags=["deals"])
app.include_router(support.router, prefix="/api/v1/support", tags=["support"])
app.include_router(providers.router, prefix="/api/v1/providers", tags=["providers"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(aggregator.router, prefix="/api/v1/aggregator", tags=["aggregator"])

workflow = compile_workflow()
grocery_workflow = compile_grocery_workflow()

from app.graph.food_pharmacy_workflow import compile_food_pharmacy_workflow
from app.graph.transit_workflow import compile_transit_workflow
from app.graph.evaluation_workflow import compile_evaluation_workflow

food_pharmacy_workflow = compile_food_pharmacy_workflow()
transit_workflow = compile_transit_workflow()
evaluation_workflow = compile_evaluation_workflow()



@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@app.get("/meta/stack")
async def stack_meta() -> dict:
    mcp = ShoppingMcpClient()
    mcp_info = mcp.runtime_info()
    tools = await mcp.list_tools()
    return {
        "langgraph": "used in app.graph.workflow.compile_workflow and app.graph.grocery_workflow.compile_grocery_workflow",
        "langchain": "used in agent executions via create_agent",
        "deepagents": "optional experimental capability for complex workflows",
        "mcp": {
            "sdk": mcp_info["mcp_library"],
            "transport": mcp_info["transport"],
            "tools": tools,
        },
    }


@app.post("/api/v1/shopping/query", response_model=ShoppingResponse)
async def shopping_query(payload: ShoppingRequest) -> ShoppingResponse:
    state = {
        "query": payload.query,
        "category": payload.category,
        "session_id": payload.session_id,
        "user_id": payload.user_id,
        "preferences": payload.preferences,
        "force_deep_agent": False,
        "context": {},
        "complexity": "simple",
        "route": "direct-tools",
        "provider_results": [],
        "recommendation": None,
        "provider_warnings": [],
        "payment_benefits": [],
        "verification": [],
        "reasoning": [],
        "response": {},
    }

    result = await workflow.ainvoke(state)
    response = ShoppingResponse(**result["response"])
    log_event("shopping_query_completed", query=payload.query, complexity=response.complexity, route=response.route)
    return response


@app.post("/api/v1/shopping/query/deep", response_model=ShoppingResponse)
async def shopping_query_deep(payload: ShoppingRequest) -> ShoppingResponse:
    """
    ⚠️  INTERNAL EVALUATION ENDPOINT ONLY
    
    This endpoint forces deep-agent mode for benchmarking and evaluation purposes.
    
    ❌ DO NOT use this as the production intelligent-routing mechanism.
    
    Purpose:
      • A/B testing Deep Agents vs LangChain agent
      • Benchmarking complex query performance
      • Evaluating reasoning quality on complex tasks
      • Internal development and debugging
    
    Production behavior:
      • The standard /api/v1/shopping/query endpoint has automatic complexity routing
      • Query complexity (not API endpoint) determines reasoning depth
      • Clients should NOT need to know about /deep endpoint
      • The UI sends normal queries; LangGraph decides if deep reasoning is needed
    
    If you're adding this endpoint to product UI or client code, STOP.
    Use /api/v1/shopping/query instead.
    """
    state = {
        "query": payload.query,
        "category": payload.category,
        "session_id": payload.session_id,
        "user_id": payload.user_id,
        "preferences": payload.preferences,
        "force_deep_agent": True,
        "context": {},
        "complexity": "complex",
        "route": "deep-agent",
        "provider_results": [],
        "recommendation": None,
        "provider_warnings": [],
        "payment_benefits": [],
        "verification": [],
        "reasoning": [],
        "response": {},
    }

    result = await workflow.ainvoke(state)
    response = ShoppingResponse(**result["response"])
    log_event("shopping_query_deep_completed", query=payload.query, complexity=response.complexity, route=response.route)
    return response


@app.post("/api/v1/grocery/query", response_model=GroceryResponse)
async def grocery_query(payload: GroceryRequest) -> GroceryResponse:
    state = {
        "items": payload.items,
        "category": payload.category,
        "session_id": payload.session_id,
        "user_id": payload.user_id,
        "preferences": payload.preferences,
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

    result = await grocery_workflow.ainvoke(state)
    response = GroceryResponse(**result["response"])
    log_event("grocery_query_completed", items=payload.items, complexity=response.complexity, route=response.route)
    return response

from app.schemas.grocery import BasketEvaluationRequest, BasketComparisonResult
from app.services.grocery.basket import BasketOptimizerService
from app.providers.canonical_catalog import get_canonical_catalog
from app.providers.grocery_registry import get_grocery_providers
from app.providers.grocery_base import normalize_grocery_results

@app.post("/api/v1/grocery/basket/evaluate", response_model=list[BasketComparisonResult])
async def evaluate_grocery_basket(payload: BasketEvaluationRequest) -> list[BasketComparisonResult]:
    catalog = get_canonical_catalog()
    catalog_map = {p.canonical_product_id: p for p in catalog}
    
    available_items = []
    providers = get_grocery_providers()
    
    # We simulate looking up these products across providers
    for item in payload.items:
        c_prod = catalog_map.get(item.canonical_product_id)
        if c_prod:
            for provider in providers:
                try:
                    # In a real app, we might query by SKU. For mock, search by title.
                    raw = await provider.search(c_prod.title, location=payload.location)
                    normalized = normalize_grocery_results(provider, raw)
                    # Force matching canonical ID for safety in mock
                    for n in normalized:
                        if c_prod.title.lower() in n.title.lower():
                            n.canonical_product_id = c_prod.canonical_product_id
                            if c_prod.image_confidence == "TRUSTED":
                                n.retailer_image_url = c_prod.image_url
                                n.image_verified = True
                                n.image_source = "canonical"
                            available_items.append(n)
                except Exception:
                    pass
                    
    results = BasketOptimizerService.evaluate(payload, available_items)
    return results
