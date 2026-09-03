import asyncio
from app.mcp.server import create_shopping_mcp_server

async def main():
    server = create_shopping_mcp_server()
    res = await server.call_tool("search_products", {"query": "test"})
    print("FastMCP.call_tool TYPE:", type(res))
    print("FastMCP.call_tool RESULT:", res)

if __name__ == "__main__":
    asyncio.run(main())
