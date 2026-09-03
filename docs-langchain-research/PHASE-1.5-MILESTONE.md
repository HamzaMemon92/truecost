# Phase 1.5: Real Data Boundary Verification

**Milestone:** Prove the full end-to-end MCP execution path works correctly

**Status:** ⏳ Planned (Do this before Phase 2)

**Estimated complexity:** Medium  
**Estimated time:** 2-3 days

---

## What Phase 1 Proved ✅

- Architecture decisions are correct
- Complexity routing is deterministic  
- Components exist and compile
- Tests pass (19/19)
- Code is well-documented

## What Phase 1.5 Must Prove

The full data flow from agent to response:

```
USER QUERY
    ↓
LANGGRAPH (validate, context, complexity gate)
    ↓
┌─────────────────────────────────────┐
│ ROUTING DECISION (complexity-based) │
└─────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────┐
│ SHOPPING AGENT (LangChain with MCP tools)        │
│                                                   │
│  LangChain Agent                                 │
│      ↓                                            │
│  Invokes MCP tool                                │
│      ↓ (CRITICAL: prove this works)              │
│  MCP Client                                      │
│      ↓                                            │
│  FastMCP Server                                  │
│      ↓                                            │
│  Provider Adapter                                │
│      ↓                                            │
│  Provider Data (or Mock as proof)                │
└──────────────────────────────────────────────────┘
    ↓
NORMALIZATION (canonical schema)
    ↓
VERIFICATION (deterministic checks)
    ↓
CONSTRAINT CHECK (policy rules)
    ↓
PAYMENT INTELLIGENCE (rewards/cashback)
    ↓
DECISION / OPTIMIZE (deterministic ranking)
    ↓
LLM SYNTHESIS (explanation)
    ↓
RESPONSE
```

**The critical unproven part:**  
Agent actually invoking MCP tools and receiving provider data (not just mock @tool returns)

---

## Specific Tasks

### Task 1: Verify Agent Actually Uses MCP Client

**Current state:**
```python
@tool
def search_products(query: str) -> str:
    _ = query
    return str(search_payload)  # ← Mock payload, not real MCP
```

**What's needed:**
Modify the tool to actually invoke the MCP client:
```python
@tool
def search_products(query: str) -> str:
    """Search via real MCP client, which connects to FastMCP server."""
    mcp_result = await mcp_client.call_tool("search_products", {"query": query})
    return str(mcp_result)  # ← Real MCP invocation
```

**Success criteria:**
- LangChain agent calls tool
- Tool invokes MCP client  
- MCP client calls FastMCP server
- FastMCP server executes provider logic
- Result returns to agent (not mock payload)

**Test needed:**
```python
def test_agent_invokes_real_mcp_tools():
    """Prove agent actually uses MCP client, not mock @tool."""
    # Call agent
    # Verify MCP tool was invoked (not just @tool wrapper)
    # Verify provider data was returned
    # Verify data is canonical schema
```

---

### Task 2: Establish Provider Abstraction Boundary

**Goal:** Make Mock Provider and Real Provider identical interfaces

**Current state:**
- Mock provider: hardcoded returns
- Real providers: awaiting credentials/implementation

**What's needed:**
```python
ShoppingProvider (abstract base)
    │
    ├── MockProvider (test/demo)
    │   def search(query) → List[CanonicalProduct]
    │
    ├── AmazonProvider (credentials pending)
    │   def search(query) → List[CanonicalProduct]
    │
    ├── FlipkartProvider (credentials pending)
    │   def search(query) → List[CanonicalProduct]
    │
    └── MyntraProvider (for future fashion category)
        def search(query) → List[CanonicalProduct]
```

**Success criteria:**
- All providers return identical `CanonicalProduct` schema
- Mock provider produces valid test data
- Real providers can be dropped in without changing agent code
- MCP tools are provider-agnostic

**Test needed:**
```python
def test_mock_provider_returns_canonical_schema():
    """Verify MockProvider outputs match CanonicalProduct exactly."""
    products = mock_provider.search("laptop")
    for product in products:
        assert isinstance(product, CanonicalProduct)
        assert product.provider is not None
        assert product.canonical_product_id is not None
```

---

### Task 3: MCP Tool Invocation Integration Test

**Goal:** Prove the full chain: Agent → MCP Client → FastMCP Server → Provider → Canonical Data

**Test template:**
```python
async def test_mcp_end_to_end_shopping_agent():
    """
    Integration test: LangChain Shopping Agent through full MCP chain.
    
    Proves:
    1. Agent invokes MCP tool
    2. MCP client calls FastMCP server
    3. FastMCP server calls provider
    4. Provider returns canonical product data
    5. Agent receives structured result
    """
    # Setup
    mcp_client = ShoppingMcpClient()
    agent = create_agent(
        model="openai:gpt-4o-mini",
        tools=_make_langchain_tools_with_real_mcp(mcp_client),
        system_prompt="..."
    )
    
    # Execute
    query = "best laptop under 100000"
    result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
    
    # Verify agent output contains reasoning about provider data
    reasoning = result.get("messages", [])[-1].content
    assert "laptop" in reasoning.lower()
    assert "price" in reasoning.lower() or "₹" in reasoning  # Contains actual product info
    
    # Verify data came from MCP, not mock @tool
    assert "MCP tool invocation" in some_debug_log or provider_was_called
```

---

### Task 4: Deterministic Calculations Separation

**Verify that ranking, payment intelligence, and verification are NOT left to LLM**

**Current need:**
```python
# GOOD: Transparent, testable, auditable
ranking_score = (
    price_factor * 0.25 +
    reviews_factor * 0.15 +
    delivery_factor * 0.10 +
    availability_factor * 0.25 +
    payment_benefits_factor * 0.25
)

# BAD: LLM decides
llm_reasoning = model.generate("Which product is best?")
best_product = llm_reasoning["choice"]  # ← Can hallucinate
```

**Success criteria:**
- Ranking uses explicit scoring formula
- Payment benefits use deterministic rules (card types, offers)
- Verification uses fact-based checks (price, availability, ratings)
- Agent reasoning is separate from deterministic calculation

**Test needed:**
```python
def test_ranking_is_deterministic_not_llm():
    """Verify ranking uses formula, not LLM hallucination."""
    product_a = CanonicalProduct(price=50000, rating=4.5, delivery="2 days")
    product_b = CanonicalProduct(price=60000, rating=4.8, delivery="1 day")
    
    # Same products should always rank the same way
    rank_1 = deterministic_ranking([product_a, product_b])
    rank_2 = deterministic_ranking([product_a, product_b])
    assert rank_1 == rank_2  # Guaranteed
    
    # Score should be explainable (not "LLM decided this")
    score = rank_1[0]["score_breakdown"]
    assert "price" in score
    assert "reviews" in score
    assert "delivery" in score
```

---

### Task 5: Canonical Schema Validation

**Verify all data flowing through system conforms to `CanonicalProduct`**

**Required fields:**
```python
CanonicalProduct:
  canonical_product_id: str        # Unique ID in our system
  provider: str                    # "amazon", "flipkart", etc.
  provider_product_id: str         # ID from that provider
  title: str
  brand: str
  category: str
  price: float                     # Current selling price
  mrp: float                       # Original/listed price
  discount: float                  # Percentage discount
  availability: str                # "in_stock", "limited", "out_of_stock"
  seller: str                      # Seller name
  rating: float                    # 0-5 star rating
  review_count: int
  delivery: str                    # "2 days", "next day", etc.
  offers: List[str]                # ["cashback", "emi", etc.]
  product_url: str
  image_url: str
  retrieved_at: datetime
  expires_at: datetime
  evidence: dict                   # {"source": "api", "timestamp": ...}
```

**Success criteria:**
- MockProvider produces valid CanonicalProduct
- Normalization doesn't lose required fields
- All downstream systems expect CanonicalProduct only
- No raw provider data reaches ranking/verification

---

## Phase 1.5 Completion Checklist

- [ ] **Integration test added:** Agent → MCP Client → FastMCP Server → Provider → CanonicalProduct
- [ ] **Provider abstraction verified:** Mock and Real follow identical interface
- [ ] **MCP tool invocation proven:** Agent actually calls MCP, not just @tool wrapper
- [ ] **Ranking deterministic:** Formula-based, not LLM-based
- [ ] **Verification deterministic:** Fact-based checks, no hallucination
- [ ] **Canonical schema validated:** All products conform to schema
- [ ] **End-to-end flow tested:** Query → Agent → MCP → Provider → Response
- [ ] **Documentation updated:** Clarify what's proven vs. what's pending
- [ ] **All tests passing:** 19 existing + 5 new integration tests
- [ ] **No production claims:** Code ready for Phase 2 pattern, not yet for production deployment

---

## What This Enables

Once Phase 1.5 is complete:

✅ **Proven pattern for all future categories**

```
Grocery
Mobility
Travel
Food
Finance
```

Each follows identical architecture:
```
LangGraph
   ↓
Complexity Gate
   ↓
Deterministic / Agent / Deep Reasoning
   ↓
MCP Tools (category-specific)
   ↓
Provider Adapters (category-specific)
   ↓
CanonicalProduct / CanonicalRide / CanonicalHotel / etc.
   ↓
Verification (category-specific checks)
   ↓
Constraint Check (policy rules)
   ↓
Payment Intelligence
   ↓
Decision / Optimize (ranking formula)
   ↓
LLM Synthesis
   ↓
Response
```

No architecture changes needed, just:
- New MCP tools
- New provider adapters
- New canonical schema variant
- New ranking formula

---

## Why NOT Yet Production-Ready

**Current state:**
- Tests pass ✅
- Architecture correct ✅
- Components compile ✅
- **Mock data flows** ✅
- **Real data flow unproven** ❌

**To claim production-ready:**
- Real end-to-end path verified ✅ (Phase 1.5 goal)
- Provider integrations working ✅ (at least mock → same interface as real)
- Deterministic calculations proven ✅
- Load testing (future milestone)
- Error handling comprehensive (future milestone)
- Observability/logging (future milestone)

---

## Timeline

**Phase 1.5 (this milestone):**
- Add 5 integration tests
- Verify MCP chain works end-to-end
- Prove deterministic calculations
- Validate canonical schema
- **Estimated: 2-3 days**

**Phase 2 (after 1.5 passing):**
- Add Grocery category (same pattern)
- Parallel: Add Mobility, Travel, Food, Finance
- **Each category: 1-2 days** (pattern already proven)

**Production deployment (future):**
- After all categories proven
- Load testing
- Error resilience
- Observability
- Security audit
- **Estimated: 1-2 weeks**

---

## Key Principle

> **Don't claim production-readiness until you've proven the real data path works, not just the mocked version.**

Phase 1 → Phase 1.5 → Phase 2 → Production

Each stage proves progressively more capability. Phase 1.5 is the gate between "architecture is correct" and "data flow actually works."

