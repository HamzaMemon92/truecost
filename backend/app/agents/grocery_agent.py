from __future__ import annotations

import json
import os
from typing import Any

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool

from app.config import settings
from app.mcp.grocery_client import GroceryMcpClient


# ============================================================================
# COMPLEXITY CLASSIFICATION
# ============================================================================


def determine_grocery_complexity(items: list[str]) -> str:
    """
    TEMPORARY Phase 2A placeholder.
    This length-based heuristic must be replaced by a robust execution policy
    that considers constraints, objectives, substitutions, and personalization.
    """
    if len(items) <= 2:
        return "simple"
    if len(items) <= 10:
        return "moderate"
    return "complex"


def choose_grocery_route(complexity: str) -> str:
    if complexity == "simple":
        return "direct-basket"
    if complexity == "moderate":
        return "grocery-agent"
    return "deep-agent"


# ============================================================================
# MODEL
# ============================================================================


def _build_model():
    if not settings.openai_api_key:
        return None

    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
    return init_chat_model(f"openai:{settings.shopping_model}")


# ============================================================================
# MCP → LANGCHAIN TOOL BRIDGE
# ============================================================================


def _make_langchain_tools(
    mcp: GroceryMcpClient,
    available_tools: list[str],
) -> list[Any]:
    tools: list[Any] = []

    if "search_items" in available_tools:
        @tool
        async def search_items(query: str) -> str:
            """Search for grocery items by query string."""
            result = await mcp.call_tool("search_items", {"query": query})
            return json.dumps(result, default=str)
        tools.append(search_items)

    if "get_item_details" in available_tools:
        @tool
        async def get_item_details(item_id: str) -> str:
            """Get detailed information for a specific grocery item."""
            result = await mcp.call_tool("get_item_details", {"item_id": item_id})
            return json.dumps(result, default=str)
        tools.append(get_item_details)

    if "get_availability" in available_tools:
        @tool
        async def get_availability(item_id: str) -> str:
            """Check grocery item stock status across providers."""
            result = await mcp.call_tool("get_availability", {"item_id": item_id})
            return json.dumps(result, default=str)
        tools.append(get_availability)

    if "get_delivery_estimate" in available_tools:
        @tool
        async def get_delivery_estimate(provider: str) -> str:
            """Get estimated delivery time and fees for a provider."""
            result = await mcp.call_tool("get_delivery_estimate", {"provider": provider})
            return json.dumps(result, default=str)
        tools.append(get_delivery_estimate)

    if "get_offers" in available_tools:
        @tool
        async def get_offers(item_id: str) -> str:
            """Get available offers or discounts for a grocery item."""
            result = await mcp.call_tool("get_offers", {"item_id": item_id})
            return json.dumps(result, default=str)
        tools.append(get_offers)

    if "get_provider_link" in available_tools:
        @tool
        async def get_provider_link(item_id: str) -> str:
            """Get the deep link for a specific grocery item."""
            result = await mcp.call_tool("get_provider_link", {"item_id": item_id})
            return json.dumps(result, default=str)
        tools.append(get_provider_link)

    return tools


# ============================================================================
# NORMAL LANGCHAIN GROCERY AGENT
# ============================================================================


async def _invoke_langchain_agent(
    items: list[str],
    mcp: GroceryMcpClient,
    available_tools: list[str],
) -> str | None:
    model = _build_model()
    if model is None:
        return None

    tools = _make_langchain_tools(mcp, available_tools)
    if not tools:
        return None

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt="""
You are the Common Master Grocery Agent.

Your ONLY job is to research grocery items and return data.

DO NOT perform math (like calculating basket totals or minimum orders).
DO NOT make final financial decisions.
DO NOT optimize the basket yourself.

Your workflow is:
1. Read the list of requested items.
2. Use tools to find each item, check availability, and check delivery options.
3. Resolve any ambiguities.
4. Return the evidence you found.

Important boundaries:
- You do not directly access external providers.
- You only use the MCP tools supplied to you.
- You do not purchase anything.
- The deterministic engine downstream will do the actual math and optimization.
""",
    )

    items_str = ", ".join(items)
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Find these items: {items_str}",
                }
            ]
        }
    )

    messages = result.get("messages", [])
    if not messages:
        return None

    last_message = messages[-1]
    content = getattr(last_message, "content", "")
    if isinstance(content, str):
        return content
    return str(content)


# ============================================================================
# OPTIONAL DEEP GROCERY AGENT
# ============================================================================


async def _invoke_deep_agent(
    items: list[str],
    mcp: GroceryMcpClient,
    available_tools: list[str],
) -> str | None:
    """
    Placeholder for Phase 2A.
    Deep Agents are optional and unimplemented in 2A.
    """
    return None


# ============================================================================
# MAIN GROCERY AGENT EXECUTION
# ============================================================================


async def run_grocery_agent_path(
    items: list[str],
    route: str,
    mcp: GroceryMcpClient,
) -> dict[str, Any]:
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
        f"Grocery execution route: {route}",
        (
            "MCP available tools: "
            + (", ".join(available_tools) if available_tools else "none")
        ),
        f"MCP runtime: {mcp_info.get('mcp_library', 'unknown')}",
    ]

    if route == "direct-basket":
        reasoning.append("Simple request: direct deterministic basket workflow.")
        mcp.call_tool = original_call_tool # type: ignore
        return {
            "reasoning": reasoning,
            "evidence": None,
            "agent_type": "none",
            "mcp_tools_used": tools_used,
            "mcp_results": mcp_results,
        }

    if route == "grocery-agent":
        reasoning.append("Moderate request: LangChain Grocery Agent selected.")
        plan = await _invoke_langchain_agent(items, mcp, available_tools)
        mcp.call_tool = original_call_tool # type: ignore

        if plan:
            reasoning.append("LangChain Grocery Agent completed its MCP tool loop.")
            if tools_used:
                reasoning.append("MCP tools used: " + ", ".join(tools_used))
                
            return {
                "reasoning": reasoning,
                "evidence": plan,
                "agent_type": "langchain",
                "mcp_tools_used": tools_used,
                "mcp_results": mcp_results,
            }
            
        reasoning.append("LangChain model unavailable; falling back.")
        return {
            "reasoning": reasoning,
            "evidence": None,
            "agent_type": "none",
            "mcp_tools_used": tools_used,
            "mcp_results": mcp_results,
        }

    if route == "deep-agent":
        reasoning.append("Complex request: Deep Agent path selected (Placeholder).")
        deep_plan = await _invoke_deep_agent(items, mcp, available_tools)
        
        if deep_plan:
            reasoning.append("Deep Agent completed the complex grocery research loop.")
            mcp.call_tool = original_call_tool # type: ignore
            if tools_used:
                reasoning.append("MCP tools used: " + ", ".join(tools_used))
                
            return {
                "reasoning": reasoning,
                "evidence": deep_plan,
                "agent_type": "deepagents",
                "mcp_tools_used": tools_used,
                "mcp_results": mcp_results,
            }

        reasoning.append("Deep Agent not available. Falling back to LangChain.")
        plan = await _invoke_langchain_agent(items, mcp, available_tools)
        mcp.call_tool = original_call_tool # type: ignore

        if plan:
            reasoning.append("LangChain Grocery Agent completed its MCP tool loop.")
            if tools_used:
                reasoning.append("MCP tools used: " + ", ".join(tools_used))
                
            return {
                "reasoning": reasoning,
                "evidence": plan,
                "agent_type": "langchain",
                "mcp_tools_used": tools_used,
                "mcp_results": mcp_results,
            }

        reasoning.append("All agents unavailable; falling back.")
        return {
            "reasoning": reasoning,
            "evidence": None,
            "agent_type": "none",
            "mcp_tools_used": tools_used,
            "mcp_results": mcp_results,
        }

    reasoning.append("Unknown route requested.")
    mcp.call_tool = original_call_tool # type: ignore
    return {
        "reasoning": reasoning,
        "evidence": None,
        "agent_type": "none",
        "mcp_tools_used": tools_used,
        "mcp_results": mcp_results,
    }
