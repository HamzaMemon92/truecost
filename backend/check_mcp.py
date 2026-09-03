import asyncio
from app.mcp.client import ShoppingMcpClient
from app.mcp.server import create_shopping_mcp_server

async def main():
    mcp = ShoppingMcpClient()
    res = await mcp.call_tool("search_products", {"query": "test"})
    print("RES:", res)
    print("TYPE:", type(res))

if __name__ == "__main__":
    asyncio.run(main())
