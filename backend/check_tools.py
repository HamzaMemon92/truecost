import asyncio
from app.mcp.client import ShoppingMcpClient

async def main():
    mcp = ShoppingMcpClient()
    tools = await mcp.list_tools()
    print("Tools:", tools)

asyncio.run(main())
