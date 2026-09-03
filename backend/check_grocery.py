import asyncio
from app.mcp.grocery_client import GroceryMcpClient
from app.mcp.grocery_server import create_grocery_mcp_server

async def main():
    mcp = GroceryMcpClient()
    res = await mcp.call_tool("search_items", {"query": "milk bread eggs"})
    print("RES:", res)
    
if __name__ == "__main__":
    asyncio.run(main())
