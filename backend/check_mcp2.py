import asyncio
from app.mcp.client import ShoppingMcpClient

async def main():
    mcp = ShoppingMcpClient()
    res = await mcp.call_tool("search_products", {"query": "test"})
    print("RES keys:", res.keys())
    print("RES result type:", type(res["result"]))
    print("RES result:", repr(res["result"]))
    
if __name__ == "__main__":
    asyncio.run(main())
