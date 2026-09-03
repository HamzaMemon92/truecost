from __future__ import annotations

from typing import Any

from app.mcp.grocery_server import create_grocery_mcp_server


class GroceryMcpClient:
    """
    A lightweight in-memory client that bridges the LangChain agent to the Grocery FastMCP server.
    
    This matches the exact pattern proven in Shopping.
    """

    def __init__(self):
        # We instantiate the FastMCP server directly to run it in-memory.
        self.server = create_grocery_mcp_server()

    async def list_tools(self) -> list[str]:
        """List all available tools from the Grocery MCP server."""
        result = await self.server.list_tools()
        # FastMCP returns the list directly; other transports wrap it in an object
        if isinstance(result, list):
            tools = result
        else:
            tools = getattr(result, "tools", [])
        names: list[str] = []
        for tool in tools:
            name = getattr(tool, "name", None)
            if isinstance(name, str):
                names.append(name)
        return sorted(names)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on the Grocery MCP server with the given arguments."""
        try:
            result = await self.server.call_tool(name, arguments)
        except Exception as exc:  # pragma: no cover
            return {"error": str(exc), "isError": True}

        # If FastMCP returns a tuple (e.g. `(list[TextContent], dict)`)
        # we extract the original python dict (second element).
        if isinstance(result, tuple) and len(result) == 2:
            second_item = result[1]
            if isinstance(second_item, dict):
                return second_item

        if isinstance(result, dict):
            return result

        content = getattr(result, "content", None)
        if content:
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if hasattr(first_item, "text"):
                    return {"result": first_item.text}
                if hasattr(first_item, "data"):
                    return {"result": first_item.data}
                return {"result": first_item}
            return {"result": content}

        if isinstance(result, (list, tuple)) and len(result) > 0:
            first_item = result[0]
            if hasattr(first_item, "text"):
                return {"result": first_item.text}
            if hasattr(first_item, "data"):
                return {"result": first_item.data}
            return {"result": first_item}

        return {"result": str(result)}

    def runtime_info(self) -> dict[str, str]:
        return {
            "mcp_library": "mcp (official Python SDK v2)",
            "transport": "in-memory (FastMCP)",
        }
