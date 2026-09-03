from __future__ import annotations

import asyncio
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.mcp.server import create_shopping_mcp_server


class ShoppingMcpClient:
    def __init__(self, server: FastMCP | None = None) -> None:
        self.server = server or create_shopping_mcp_server()

    async def list_tools(self) -> list[str]:
        """List all available tools from the MCP server."""
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
        """Call a tool on the MCP server with the given arguments."""
        try:
            result = await self.server.call_tool(name, arguments)
        except Exception as exc:  # pragma: no cover - defensive error handling
            return {"error": "Tool execution failed", "details": str(exc)}

        if isinstance(result, dict):
            return result

        if hasattr(result, "text"):
            return {"result": result.text}

        if hasattr(result, "data"):
            return {"result": result.data}

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

        return {"error": "No content in tool response"}

    def runtime_info(self) -> dict[str, Any]:
        return {
            "mcp_library": "mcp (official Python SDK v2)",
            "transport": "in-memory server for local orchestration",
        }
