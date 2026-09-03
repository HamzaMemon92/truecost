# Phase 1 architecture research notes

## LangChain and LangGraph guidance

- LangGraph is the orchestration layer: it owns state, transitions, routing, retries, and workflow control.
- LangChain is the agent/tool/LLM construction layer: it is appropriate for tool-backed reasoning and bounded planning.
- Deep research or deep agents should be used only for moderate and complex tasks where tool use, multi-step reasoning, and uncertainty handling justify the extra latency and cost.
- Deterministic services should remain deterministic for pricing, ranking, recommendation math, verification, and any arithmetic-heavy logic.

Official source notes used:
- LangChain overview: https://docs.langchain.com/oss/python/langchain/overview
- LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview
- MCP introduction: https://modelcontextprotocol.io/introduction
- MCP architecture: https://modelcontextprotocol.io/docs/learn/architecture

Observed guidance from docs:
- LangChain agents are built on top of LangGraph and can be incrementally composed with tools and middleware.
- LangGraph is explicitly positioned for mixing deterministic and agentic steps, with durable execution and HITL support.
- Deep Agents are a higher-level harness and should be applied selectively rather than for every request.
- MCP uses explicit tool discovery (`tools/list`) and bounded tool execution (`tools/call`) with typed schemas.

MCP library decision:
- Use the official MCP Python SDK package: `mcp` (v2 line, python-sdk repository).
- Reason: it is the protocol-maintained implementation with first-class client/server APIs, transport support, and versioned spec compatibility.
- FastMCP note: in this backend we switched to the official `mcp.server.MCPServer` pattern from SDK docs to keep alignment with current SDK guidance.

Deep Agents compatibility note:
- `deepagents` currently requires Python >= 3.11.
- This workspace interpreter is Python 3.10, so deep-agent execution is implemented with graceful runtime fallback.
- On Python 3.11+, install dependencies and the deep-agent path will execute via `create_deep_agent`.

## MCP guidance

- MCP is the standard boundary between an agent and external tools or provider systems.
- It should be treated as a capability-scoped layer, not as a free-form network access path.
- The ShoppingAgent should only receive the tools it is explicitly allowed to use.

## Implementation decision for this project

- The UI remains TypeScript/TanStack Start.
- The server-side orchestration uses a real server boundary and LangGraph-based state routing.
- The workflow is intentionally bounded: simple queries stay direct, complex queries trigger the shopping agent path.
- When AI API credentials are missing, the system falls back gracefully to deterministic mock/live-safe logic rather than silently fabricating provider data.

## One important rule

Do not turn every function into an agent. Use deep reasoning only where the workflow genuinely benefits from it. For shopping comparisons, deterministic scoring and verification remain the source of truth; the LLM should explain and reason, not become the arithmetic engine.

## Phase 1 gating policy used in implementation

- `simple` queries: deterministic path (`direct-tools`) only.
- `moderate` queries: `shopping-agent` path with bounded MCP tool access.
- `complex` queries: `deep-agent` path with extra multi-constraint reasoning, still bounded to the same MCP capability surface.
