import asyncio
from app.mcp.server import create_shopping_mcp_server

async def main():
    server = create_shopping_mcp_server()
    result = await server.list_tools()
    print("Result type:", type(result))
    print("Result:", result)
    tools = getattr(result, "tools", None)
    print("tools attr:", tools)
    # Try as a list directly
    if isinstance(result, list):
        print("Result is a list of", len(result), "items")
        for item in result:
            print("  item:", item, type(item))

asyncio.run(main())
