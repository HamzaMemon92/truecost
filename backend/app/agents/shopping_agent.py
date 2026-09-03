from __future__ import annotations

import json
import os
from typing import Any

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool

from app.config import policy, settings
from app.mcp.client import ShoppingMcpClient


# ============================================================================
# OPTIONAL DEEP AGENTS
# ============================================================================
#
# Deep Agents is an OPTIONAL reasoning harness for genuinely complex
# shopping/research requests.
#
# Architecture:
#
#   LangGraph
#       |
#       +-- SIMPLE
#       |      -> deterministic/direct workflow
#       |
#       +-- MODERATE
#       |      -> LangChain Shopping Agent
#       |
#       +-- COMPLEX
#              -> Deep Agent
#                    |
#                    +-- built-in planning/context capabilities
#                    +-- MCP shopping tools
#                    +-- optional subagents later
#              -> LangChain fallback if Deep Agents unavailable
#
# Important:
#
#   LangGraph = application orchestration
#   LangChain = agent/tool-calling abstraction
#   Deep Agents = optional complex-task harness
#   MCP = external capability/data boundary
#
# Deep Agents does NOT replace LangGraph.
# Deep Agents itself uses LangGraph/LangChain internally.
#
# ============================================================================

try:
    from deepagents import create_deep_agent
except Exception:
    create_deep_agent = None


# ============================================================================
# COMPLEXITY CLASSIFICATION
# ============================================================================


def determine_complexity(query: str) -> str:
    """
    Determine the reasoning depth required for a shopping request.

    This is intentionally deterministic.

    It does NOT:
        - call an LLM
        - call MCP
        - call a provider
        - perform shopping research

    It only decides how much reasoning machinery is appropriate.
    """

    normalized = query.strip().lower()

    if not normalized:
        return "simple"

    score = 0

    for signal in policy.moderate_keywords:
        if signal in normalized:
            score += 1

    if (
        score >= policy.complex_keyword_multiplier
        or len(normalized.split()) >= policy.long_query_tokens
    ):
        return "complex"

    if score >= 1:
        return "moderate"

    return "simple"


def choose_route(complexity: str) -> str:
    """
    Convert complexity into the application-level execution route.

    IMPORTANT:

        The route is selected by query characteristics.

        Python version / library availability does NOT change the intended
        route.

    Runtime availability only determines whether the optional Deep Agent
    implementation can execute after the route has already been selected.
    """

    normalized = complexity.strip().lower()

    if normalized == "simple":
        return "direct-tools"

    if normalized == "moderate":
        return "shopping-agent"

    if normalized == "complex":
        return "deep-agent"

    # Defensive fallback.
    return "shopping-agent"


# ============================================================================
# MODEL
# ============================================================================


def _build_model():
    """
    Construct the configured LangChain chat model.

    The same model abstraction can be supplied to:
        - LangChain create_agent()
        - Deep Agents create_deep_agent()

    No inference occurs here.
    """

    if not settings.openai_api_key:
        return None

    os.environ.setdefault(
        "OPENAI_API_KEY",
        settings.openai_api_key,
    )

    return init_chat_model(
        f"openai:{settings.shopping_model}",
    )


# ============================================================================
# MCP → LANGCHAIN TOOL BRIDGE
# ============================================================================


def _make_langchain_tools(
    mcp: ShoppingMcpClient,
    available_tools: list[str],
) -> list[Any]:
    """
    Convert the MCP capability surface into bounded LangChain tools.

    Architecture:

        Shopping Agent
              |
              v
        LangChain Tool
              |
              v
        ShoppingMcpClient
              |
              v
          MCP Server
              |
              v
        Provider Adapter
              |
              v
       Amazon / Flipkart / etc.

    The agent never directly accesses provider APIs.
    """

    tools: list[Any] = []

    # ------------------------------------------------------------------
    # Product search
    # ------------------------------------------------------------------

    if "search_products" in available_tools:

        @tool
        async def search_products(query: str) -> str:
            """
            Search available shopping providers for products.

            Use this when external product discovery is required.
            """

            result = await mcp.call_tool(
                "search_products",
                {
                    "query": query,
                },
            )

            return json.dumps(
                result,
                default=str,
            )

        tools.append(search_products)

    # ------------------------------------------------------------------
    # Product details
    # ------------------------------------------------------------------

    if "get_product_details" in available_tools:

        @tool
        async def get_product_details(product_id: str) -> str:
            """
            Retrieve detailed information about a specific product.
            """

            result = await mcp.call_tool(
                "get_product_details",
                {
                    "product_id": product_id,
                },
            )

            return json.dumps(
                result,
                default=str,
            )

        tools.append(get_product_details)

    # ------------------------------------------------------------------
    # Price
    # ------------------------------------------------------------------

    if "get_price" in available_tools:

        @tool
        async def get_price(product_id: str) -> str:
            """
            Retrieve current provider pricing for a product.
            """

            result = await mcp.call_tool(
                "get_price",
                {
                    "product_id": product_id,
                },
            )

            return json.dumps(
                result,
                default=str,
            )

        tools.append(get_price)

    # ------------------------------------------------------------------
    # Reviews
    # ------------------------------------------------------------------

    if "get_reviews" in available_tools:

        @tool
        async def get_reviews(product_id: str) -> str:
            """
            Retrieve review/rating information for a product.
            """

            result = await mcp.call_tool(
                "get_reviews",
                {
                    "product_id": product_id,
                },
            )

            return json.dumps(
                result,
                default=str,
            )

        tools.append(get_reviews)

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------

    if "get_availability" in available_tools:

        @tool
        async def get_availability(product_id: str) -> str:
            """
            Retrieve current availability information.
            """

            result = await mcp.call_tool(
                "get_availability",
                {
                    "product_id": product_id,
                },
            )

            return json.dumps(
                result,
                default=str,
            )

        tools.append(get_availability)

    # ------------------------------------------------------------------
    # Delivery
    # ------------------------------------------------------------------

    if "get_delivery" in available_tools:

        @tool
        async def get_delivery(product_id: str) -> str:
            """
            Retrieve delivery/ETA information.
            """

            result = await mcp.call_tool(
                "get_delivery",
                {
                    "product_id": product_id,
                },
            )

            return json.dumps(
                result,
                default=str,
            )

        tools.append(get_delivery)

    # ------------------------------------------------------------------
    # Offers
    # ------------------------------------------------------------------

    if "get_offers" in available_tools:

        @tool
        async def get_offers(product_id: str) -> str:
            """
            Retrieve currently available offers for a product.
            """

            result = await mcp.call_tool(
                "get_offers",
                {
                    "product_id": product_id,
                },
            )

            return json.dumps(
                result,
                default=str,
            )

        tools.append(get_offers)

    return tools


# ============================================================================
# NORMAL LANGCHAIN SHOPPING AGENT
# ============================================================================


async def _invoke_langchain_agent(
    query: str,
    mcp: ShoppingMcpClient,
    available_tools: list[str],
) -> str | None:
    """
    Run the normal Shopping Agent.

    LangChain's create_agent() implements the actual agent loop:

        model
          ↓
        decide
          ↓
        tool call?
        /      \
      yes       no
       |         |
       v         v
      tool     final
       |
       v
    tool result
       |
       └──────> model again

    Therefore we intentionally DO NOT pre-call search_products().
    """

    model = _build_model()

    if model is None:
        return None

    tools = _make_langchain_tools(
        mcp,
        available_tools,
    )

    if not tools:
        return None

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt="""
You are the Common Master Shopping Agent.

You are a specialist reasoning agent inside a larger LangGraph workflow.

Your responsibility is to investigate shopping requests using the MCP
capabilities made available to you.

Your workflow is:

1. Understand the user's shopping objective.
2. Identify constraints and comparison criteria.
3. Decide which MCP capability is required.
4. Call the appropriate MCP tool.
5. Inspect the returned evidence.
6. Decide whether additional evidence is required.
7. Perform additional MCP calls only when useful.
8. Distinguish factual provider data from reasoning.
9. Never invent prices, availability, reviews, offers or delivery information.
10. Return a concise evidence-based shopping strategy.

Important boundaries:

- You do not directly access Amazon, Flipkart, or other providers.
- You only use the MCP tools supplied to you.
- You do not purchase anything.
- You do not book anything.
- You do not execute payments.
- You do not override deterministic ranking or policy decisions.
- Do not fabricate unavailable information.

Prefer evidence collected through MCP over assumptions.
""",
    )

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": query,
                }
            ]
        }
    )

    messages = result.get(
        "messages",
        [],
    )

    if not messages:
        return None

    last_message = messages[-1]

    content = getattr(
        last_message,
        "content",
        "",
    )

    if isinstance(content, str):
        return content

    return str(content)


# ============================================================================
# OPTIONAL DEEP SHOPPING AGENT
# ============================================================================


async def _invoke_deep_agent(
    query: str,
    mcp: ShoppingMcpClient,
    available_tools: list[str],
) -> str | None:
    """
    Run the optional Deep Agent for genuinely complex shopping research.

    Deep Agents provides capabilities that are useful when a task becomes
    multi-step and context-heavy:

        - built-in planning
        - context management
        - optional subagents
        - tool-calling loop
        - LangGraph runtime underneath

    For Common Master, however, the agent is intentionally given only the
    shopping MCP capability surface needed for this task.

    We do NOT expose host filesystem/shell capabilities from this function.

    Deep Agent is also mutually exclusive with the normal LangChain Agent
    for a single request.
    """

    if create_deep_agent is None:
        return None

    model = _build_model()

    if model is None:
        return None

    tools = _make_langchain_tools(
        mcp,
        available_tools,
    )

    if not tools:
        return None

    deep_agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt="""
You are Common Master's advanced Shopping Research Agent.

You are invoked only for complex shopping requests where multiple constraints,
providers, products and trade-offs may need to be investigated.

Your goal is NOT merely to search once.

You should:

1. Understand the complete shopping objective.
2. Break the problem into meaningful research tasks.
3. Decide what evidence is needed.
4. Use the available MCP shopping tools.
5. Inspect results critically.
6. Perform additional tool calls when evidence is incomplete.
7. Compare meaningful trade-offs.
8. Avoid unsupported assumptions.
9. Produce a concise evidence-based research strategy.

Important boundaries:

- Provider information must come from MCP tools.
- Never invent prices, ratings, availability, delivery times or offers.
- Never purchase anything.
- Never book anything.
- Never execute payment operations.
- Never bypass provider authorization.
- Deterministic calculations and policy decisions belong to the surrounding
  application workflow.

Your output should summarize the research findings and trade-offs, not expose
internal chain-of-thought.
""",
    )

    result = await deep_agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": query,
                }
            ]
        }
    )

    messages = result.get(
        "messages",
        [],
    )

    if not messages:
        return None

    last_message = messages[-1]

    content = getattr(
        last_message,
        "content",
        "",
    )

    if isinstance(content, str):
        return content

    return str(content)


# ============================================================================
# MAIN SHOPPING AGENT EXECUTION
# ============================================================================


async def run_agent_path(
    query: str,
    route: str,
    mcp: ShoppingMcpClient,
) -> dict[str, Any]:
    """
    Execute the selected reasoning path.

    IMPORTANT:

        This function is NOT the entire LangGraph.

    The parent LangGraph should own:

        validate
          ↓
        understand
          ↓
        complexity gate
          ↓
        category route
          ↓
        this specialist execution
          ↓
        normalize
          ↓
        verify
          ↓
        deterministic ranking
          ↓
        response

    This function owns only the Shopping Agent execution layer.
    """

    # ------------------------------------------------------------------
    # Discover the MCP capability surface.
    # ------------------------------------------------------------------

    available_tools = await mcp.list_tools()
    
    tools_used: list[str] = []
    mcp_results: list[dict[str, Any]] = []
    
    original_call_tool = mcp.call_tool
    async def capture_call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        res = await original_call_tool(name, arguments)
        tools_used.append(name)
        if isinstance(res, dict):
            mcp_results.append(res)
        return res
        
    mcp.call_tool = capture_call_tool # type: ignore

    mcp_info = mcp.runtime_info()

    reasoning: list[str] = [
        f"Shopping execution route: {route}",
        (
            "MCP available tools: "
            + (
                ", ".join(available_tools)
                if available_tools
                else "none"
            )
        ),
        f"MCP runtime: {mcp_info.get('mcp_library', 'unknown')}",
    ]

    # ==================================================================
    # SIMPLE
    # ==================================================================
    #
    # No LLM agent.
    #
    # The parent LangGraph workflow should execute the deterministic
    # provider-search path.
    # ==================================================================

    if route == "direct-tools":

        reasoning.append(
            "Simple request: direct deterministic provider workflow."
        )

        mcp.call_tool = original_call_tool # type: ignore
        return {
            "reasoning": reasoning,
            "evidence": None,
            "agent_type": "none",
            "mcp_tools_used": tools_used,
            "mcp_results": mcp_results,
        }

    # ==================================================================
    # MODERATE
    # ==================================================================
    #
    # Exactly one LangChain Shopping Agent.
    # ==================================================================

    if route == "shopping-agent":

        reasoning.append(
            "Moderate request: LangChain Shopping Agent selected."
        )

        plan = await _invoke_langchain_agent(
            query=query,
            mcp=mcp,
            available_tools=available_tools,
        )

        mcp.call_tool = original_call_tool # type: ignore

        if plan:

            reasoning.append(
                "LangChain Shopping Agent completed its MCP tool loop."
            )

            if tools_used:
                reasoning.append(
                    "MCP tools used: " + ", ".join(tools_used)
                )

            return {
                "reasoning": reasoning,
                "evidence": plan,
                "agent_type": "langchain",
                "mcp_tools_used": tools_used,
                "mcp_results": mcp_results,
            }

        reasoning.append(
            "LangChain model unavailable; parent workflow should continue "
            "with its deterministic fallback."
        )

        return {
            "reasoning": reasoning,
            "evidence": None,
            "agent_type": "none",
            "mcp_tools_used": tools_used,
            "mcp_results": mcp_results,
        }

    # ==================================================================
    # COMPLEX
    # ==================================================================
    #
    # Deep Agent is preferred for the complex route.
    #
    # If unavailable, use LangChain.
    #
    # NEVER run both for the same production request.
    # ==================================================================

    if route == "deep-agent":

        reasoning.append(
            "Complex request: Deep Agent path selected."
        )

        deep_plan = await _invoke_deep_agent(
            query=query,
            mcp=mcp,
            available_tools=available_tools,
        )

        if deep_plan:

            reasoning.append(
                "Deep Agent completed the complex shopping research loop."
            )

            mcp.call_tool = original_call_tool # type: ignore
            return {
                "reasoning": reasoning,
                "evidence": deep_plan,
                "agent_type": "deep-agent",
                "mcp_tools_used": tools_used,
                "mcp_results": mcp_results,
            }

        # --------------------------------------------------------------
        # Optional Deep Agent unavailable.
        #
        # Fallback to normal LangChain agent.
        # --------------------------------------------------------------

        reasoning.append(
            "Deep Agent unavailable; using LangChain Shopping Agent fallback."
        )

        fallback_plan = await _invoke_langchain_agent(
            query=query,
            mcp=mcp,
            available_tools=available_tools,
        )

        mcp.call_tool = original_call_tool # type: ignore

        if fallback_plan:

            reasoning.append(
                "LangChain fallback completed the MCP tool loop."
            )

            return {
                "reasoning": reasoning,
                "evidence": fallback_plan,
                "agent_type": "langchain-fallback",
                "mcp_tools_used": tools_used,
                "mcp_results": mcp_results,
            }

        reasoning.append(
            "No reasoning model available; parent workflow should use "
            "deterministic fallback."
        )

        return {
            "reasoning": reasoning,
            "evidence": None,
            "agent_type": "none",
            "mcp_tools_used": tools_used,
            "mcp_results": mcp_results,
        }

    # ==================================================================
    # UNKNOWN ROUTE
    # ==================================================================

    reasoning.append(
        f"Unknown route '{route}'; using safe LangChain fallback."
    )

    fallback_plan = await _invoke_langchain_agent(
        query=query,
        mcp=mcp,
        available_tools=available_tools,
    )

    mcp.call_tool = original_call_tool # type: ignore

    return {
        "reasoning": reasoning,
        "evidence": fallback_plan,
        "agent_type": (
            "langchain-fallback"
            if fallback_plan
            else "none"
        ),
        "mcp_tools_used": tools_used,
        "mcp_results": mcp_results,
    }
