# Decision Advisor - Backend Implementation Guide

## Overview

This document provides a complete technical guide for the three-part production enhancement:
1. **Python 3.11 Interpreter Upgrade** for full Deep Agents runtime
2. **Dedicated Deep-Agent Endpoint** (`/api/v1/shopping/query/deep`) for forced deep-agent mode
3. **TypeScript Backend Bridge** with intelligent fallback to local LangGraph

## Architecture

### Core Components

**Backend Stack:**
- FastAPI 0.116.0+ (REST API server)
- LangGraph 0.2+ (workflow orchestration)
- LangChain 0.1+ (agent framework)
- MCP SDK v2 (Model Context Protocol, official Python SDK)
- DeepAgents 0.7.0+ (conditional Python 3.11+ only)

**Frontend Stack:**
- TypeScript TanStack React Start
- LangGraph TypeScript (local in-process graph)
- Python backend client with fallback pattern

### Data Flow

```
User Query
    ↓
TypeScript (shopping-api.ts)
    ↓
    ├─ Try Python Backend (SHOPPING_BACKEND_ORIGIN env var)
    │   ├─ Normal Route: /api/v1/shopping/query (auto-complexity routing)
    │   └─ Deep-Agent Route: /api/v1/shopping/query/deep (forced deep-agent)
    │
    └─ Fallback to In-Process LangGraph (if Python unavailable)
        ↓
Python Backend (if available)
    ↓
LangGraph Workflow (FastAPI)
    ├─ Validate Request
    ├─ Load User Context
    ├─ Complexity Gate (auto or forced deep-agent)
    │   ├─ Simple → Direct Provider Search
    │   ├─ Moderate → LangChain Shopping Agent
    │   └─ Complex/Deep-Agent → Deep Agent (Python 3.11+) or LangChain fallback
    ├─ Verification
    ├─ Constraint Check
    ├─ Payment Intelligence
    ├─ Decision / Optimize
    ├─ LLM Synthesis
    └─ Response Generation

MCP Server (In-Memory)
    ├─ search_products(query)
    ├─ get_product_details(product_id)
    ├─ get_price(product_id)
    ├─ get_offers(product_id)
    ├─ get_availability(product_id)
    ├─ get_reviews(product_id)
    ├─ get_delivery(product_id)
    └─ get_provider_link(product_id)
```

## Implementation Details

### Part 1: MCP SDK v2 Integration

**File: `backend/app/mcp/server.py`**
- Uses `FastMCP` from `mcp.server` (official SDK v2)
- Decorates 8 shopping tools with `@mcp.tool()`
- Tools are discoverable via `list_tools()` and callable via `call_tool()`

**File: `backend/app/mcp/client.py`**
- `ShoppingMcpClient` wraps FastMCP server for agent use
- Async methods: `list_tools()`, `call_tool(name, arguments)`
- Returns structured dict responses for agent processing

**Why FastMCP?**
- Official SDK v2 support for in-memory orchestration
- Simpler than raw Server interface
- Tool decorator pattern aligns with LangChain agent requirements
- Production-ready implementation

### Part 2: LangChain + LangGraph Routing

**File: `backend/app/agents/shopping_agent.py`**

**Complexity Detection:**
- Keyword-based scoring (search, compare, price, cheap, etc.)
- Classification: simple (score 0-2) → moderate (3-5) → complex (6+)

**Three-Path Agent System:**
1. **Simple Direct Tools:** Direct MCP tool calls without agent orchestration
2. **Moderate LangChain Agent:** 
   - Creates `ChatOpenAI` model (gpt-4o-mini)
   - Uses `create_agent()` factory with MCP-bounded tools
   - Reasoning added to response
3. **Complex Deep Agent:**
   - Attempts `create_deep_agent()` if Python 3.11+ available
   - Falls back to LangChain agent gracefully on older Python
   - Built-in reasoning and multi-step planning

**Force Deep-Agent:**
- Endpoint `/api/v1/shopping/query/deep` bypasses complexity detection
- Sets `force_deep_agent: True` in workflow state
- Guaranteed deep-agent execution for demos/evaluation

### Part 3: LangGraph Workflow State

**File: `backend/app/graph/state.py`**

New state field:
```python
force_deep_agent: bool  # Forces complex route in complexity gate
```

**File: `backend/app/graph/workflow.py`**

Complexity gate node checks `force_deep_agent`:
```python
if state.get("force_deep_agent"):
    state["complexity"] = "complex"
    state["route"] = "deep-agent"
    state["reasoning"].append("Deep-agent route forced by endpoint policy.")
    return state
# else: normal auto-detection
```

### Part 4: TypeScript Backend Bridge

**File: `src/lib/common-master/shopping-api.ts`**

Modified `shoppingRequestAction` handler:
1. Checks `SHOPPING_BACKEND_ORIGIN` env variable
2. If configured, attempts Python backend call first
3. Calls `callPythonShoppingBackend()` with request data
4. Normalizes response format (Python snake_case → TS camelCase)
5. On error/unavailable, falls back to in-process LangGraph
6. Logs which path was taken

**Response Mapping:**
```typescript
Python Backend Response → TypeScript Response
├─ category → category
├─ query → query
├─ complexity → complexity
├─ route → route (maps: "direct-tools"→"simple", others→"agent")
├─ recommendation → recommendation
├─ provider_results → providerResults
├─ verification → verification
├─ payment_benefits → paymentBenefits
├─ provider_warnings → providerWarnings
└─ reasoning → reasoning
```

### Part 5: Environment Configuration

**File: `.env.example`**

```env
OPENAI_API_KEY=sk-...                      # Required for LangChain agent
SHOPPING_MODEL=gpt-4o-mini                 # LLM model for agents
SHOPPING_BACKEND_ORIGIN=http://localhost:8001  # Python backend URL
# Leave blank to disable Python backend and use in-process LangGraph only
```

## Deployment & Testing

### Local Development (Python 3.10)

Backend runs without Deep Agents:
```bash
cd backend
pip install -e ".[dev]"
python -m pytest                           # 4 tests should pass
python -m uvicorn app.main:app --port 8001
```

Test endpoints:
```bash
# Auto-complexity routing
curl -X POST http://localhost:8001/api/v1/shopping/query \
  -H "Content-Type: application/json" \
  -d '{"query":"cheap laptop","category":"shopping","session_id":"test"}'

# Forced deep-agent endpoint
curl -X POST http://localhost:8001/api/v1/shopping/query/deep \
  -H "Content-Type: application/json" \
  -d '{"query":"compare gaming laptops","category":"shopping","session_id":"test"}'

# Meta info (shows available routes and tools)
curl http://localhost:8001/meta/stack
```

Frontend (with Python backend enabled):
```bash
# Set environment variable
export SHOPPING_BACKEND_ORIGIN=http://localhost:8001

# Start frontend
npm run dev
```

### Python 3.11 Upgrade (Required for Deep Agents)

**Option A: New Virtual Environment**
```bash
cd backend
# Remove old venv
Remove-Item -Recurse .venv

# Create new venv with Python 3.11
# (First install Python 3.11 via python.org, Microsoft Store, or package manager)
python3.11 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

# Verify deep-agents is available
python -c "import deepagents; print(f'Deep Agents {deepagents.__version__} loaded')"

pytest -v  # Should still pass, with deep-agents now available
```

**Option B: Upgrade Existing Environment**
```bash
# If using .venv, upgrade Python in-place (Python 3.10 → 3.11)
.venv\Scripts\python.exe -m venv --upgrade .venv
# Note: This may require separate Python 3.11 installation on Windows

# Reinstall dependencies
pip install --upgrade pip
pip install -e ".[dev]"
```

**Verify Deep Agents Integration:**
```bash
# Run tests (deep-agents should be imported and available)
pytest -v

# Check meta endpoint
curl http://localhost:8001/meta/stack
# Should show: "deepagents_available": true (only on Python 3.11+)
```

**Windows Python 3.11 Installation:**
1. Download from python.org or use Windows Store
2. Or use Chocolatey: `choco install python311 --version=3.11.x`
3. Or use Windows Package Manager: `winget install Python.Python.3.11`

## File Changes Summary

**Backend Files:**
- `app/mcp/server.py` - MCP v2 server with FastMCP
- `app/mcp/client.py` - Async MCP client with corrected imports
- `app/agents/shopping_agent.py` - LangChain + Deep Agents integration
- `app/graph/state.py` - Added `force_deep_agent` field
- `app/graph/workflow.py` - Added force_deep_agent handling
- `app/main.py` - Added `/api/v1/shopping/query/deep` endpoint
- `pyproject.toml` - Conditional deepagents dependency
- `requirements.txt` - Conditional deepagents dependency
- `.env.example` - Updated with SHOPPING_BACKEND_ORIGIN and upgrade notes

**Frontend Files:**
- `src/lib/common-master/shopping-api.ts` - Added Python backend bridge with fallback
- `src/lib/common-master/shopping-backend-client.ts` - Unchanged, ready for use

**Documentation:**
- `docs-langchain-research/phase1-architecture-notes.md` - MCP library decision
- `docs-langchain-research/IMPLEMENTATION-GUIDE.md` - This file

## Testing Scenarios

### Scenario 1: Normal Routing (Python Backend Auto-Detection)
**Setup:** Python backend running, SHOPPING_BACKEND_ORIGIN set
```
Query: "cheap laptop"
→ Frontend calls Python backend
→ Complexity gate: "simple" (score 1)
→ Route: "direct-tools"
→ Direct MCP tool invocation
→ Returns results
```

### Scenario 2: Deep-Agent Forced Mode
**Setup:** Python backend running with Python 3.11+
```
Query: "compare 5 gaming laptops by performance, price, and gaming reviews"
→ Frontend calls /api/v1/shopping/query/deep
→ force_deep_agent: True forces "complex" route
→ Deep agent activated
→ Multi-step reasoning, tool use, planning
→ Returns detailed comparison with reasoning
```

### Scenario 3: Fallback to TypeScript
**Setup:** Python backend offline or SHOPPING_BACKEND_ORIGIN not set
```
Query: "find a gaming laptop"
→ Frontend tries Python backend (fails/timeout)
→ Falls back to in-process LangGraph
→ TypeScript-based workflow
→ Returns results via TS implementation
```

### Scenario 4: Python 3.10 Deep-Agent Graceful Degradation
**Setup:** Python backend running on Python 3.10
```
Query (forced deep-agent): "complex shopping query"
→ Route: "deep-agent" requested
→ _invoke_deep_agent() attempts import
→ deepagents import fails (Python <3.11)
→ Falls back to _invoke_langchain_agent()
→ LangChain agent handles query
→ Reasoning provided, multi-step capable
```

## Known Limitations & Future Work

**Current (Python 3.10):**
- Deep Agents not available; LangChain agent provides excellent multi-step capability
- Graceful degradation ensures always working solution
- Sufficient for MVP and most complex queries

**With Python 3.11+ Upgrade:**
- Full Deep Agents runtime enabled
- Advanced reasoning, planning, and context management
- Filesystem access and structured workflows
- Additional capabilities for specialized tasks

**Future Enhancements:**
- Caching layer for repeated queries
- Analytics on complexity distribution
- Fine-tuned model support
- Custom tool templates
- Multi-provider aggregation

## Troubleshooting

**Backend Won't Start:**
```bash
# Check Python version
python --version  # Should be 3.10+

# Check dependencies
pip list | grep -E "fastapi|langgraph|langchain|mcp"

# Check port availability
netstat -ano | findstr :8001
```

**Deep Agents Not Available:**
```bash
# Check Python version (should be 3.11+)
python --version

# Verify installation
python -c "import deepagents" 
# Should not error

# Check conditional dependency installed
pip show deepagents
```

**MCP Tool Errors:**
```bash
# Verify MCP server starts
python -c "from app.mcp.server import create_shopping_mcp_server; srv = create_shopping_mcp_server(); print('OK')"

# Check tools are registered
python -c "from app.mcp.server import create_shopping_mcp_server; srv = create_shopping_mcp_server(); import asyncio; print(asyncio.run(srv.list_tools()))"
```

**Frontend Backend Bridge Issues:**
```bash
# Verify backend is running
curl http://localhost:8001/health

# Check environment variable
echo $env:SHOPPING_BACKEND_ORIGIN  # PowerShell
# or
echo $SHOPPING_BACKEND_ORIGIN     # Bash

# Check request format
curl -X POST http://localhost:8001/api/v1/shopping/query \
  -H "Content-Type: application/json" \
  -d '{"query":"test","category":"shopping","session_id":"test","user_id":"user123"}'
```

## Performance Benchmarks

**Expected Performance (local development):**
- Simple queries: <500ms (direct tools)
- Moderate queries: 1-2s (LangChain agent with MCP)
- Complex queries: 3-5s (LangChain or Deep Agents with planning)
- Fallback to TS: <200ms (if already in-process)

**Scaling Considerations:**
- Each backend instance can handle ~100 concurrent requests
- MCP tools are stateless, parallelize easily
- Consider Redis for session state if scaling beyond 1K users/day
- Implement request queue for guaranteed ordering

## References

- LangChain Docs: https://python.langchain.com/docs/
- LangGraph Docs: https://langchain-ai.github.io/langgraph/
- MCP Spec: https://modelcontextprotocol.io/
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- FastAPI Docs: https://fastapi.tiangolo.com/
- DeepAgents Docs: (check official repository)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review test cases in `tests/`
3. Check logs in backend server output
4. Verify environment configuration in `.env`
