from __future__ import annotations

import pytest

from app.graph.workflow import _provider_search
from app.mcp.client import ShoppingMcpClient
from app.providers.mock_provider import MockProvider


@pytest.mark.asyncio
async def test_mcp_client_handles_tool_unavailable_gracefully():
    class FailingServer:
        async def call_tool(self, name: str, arguments: dict[str, str]):
            raise RuntimeError("MCP tool unavailable")

    client = ShoppingMcpClient(server=FailingServer())
    result = await client.call_tool("search_products", {"query": "laptop"})

    assert result["error"] == "Tool execution failed"
    assert "MCP tool unavailable" in result["details"]


@pytest.mark.asyncio
async def test_provider_search_skips_unavailable_provider_and_keeps_valid_results(monkeypatch):
    class ExplodingProvider:
        name = "broken"
        status = "live"

        async def search(self, query: str):
            raise RuntimeError("provider offline")

    state = {
        "query": "laptop",
        "provider_results": [],
        "provider_warnings": [],
    }

    monkeypatch.setattr("app.graph.workflow.get_providers", lambda: [ExplodingProvider(), MockProvider()])

    await _provider_search(state)

    assert len(state["provider_results"]) >= 1
    assert any("provider" in warning.lower() and "offline" in warning.lower() for warning in state["provider_warnings"])


@pytest.mark.asyncio
async def test_provider_search_rejects_malformed_provider_response(monkeypatch):
    class MalformedProvider:
        name = "malformed"
        status = "live"

        async def search(self, query: str):
            return [{"bad": "data"}]

    state = {
        "query": "laptop",
        "provider_results": [],
        "provider_warnings": [],
    }

    monkeypatch.setattr("app.graph.workflow.get_providers", lambda: [MalformedProvider()])

    await _provider_search(state)

    assert state["provider_results"] == []
    assert state["provider_warnings"]
    assert any("malformed" in warning.lower() or "invalid" in warning.lower() for warning in state["provider_warnings"])
