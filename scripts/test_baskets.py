import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import asyncio
from app.mcp.grocery_client import GroceryMcpClient
from app.graph.grocery_workflow import compile_grocery_workflow

async def main():
    mcp_client = GroceryMcpClient()
    queries = ["Red Bull", "Thums Up", "Nutella", "Oreo", "Dairy Milk"]
    for q in queries:
        res = await mcp_client.call_tool("search_items", {"query": q})
        print(f"Query '{q}': {len(res.get('items', []))} items")
        for i in res.get('items', [])[:3]:
            print("  ", i.get('provider'), i.get('title'), i.get('er_decision'))
            
    workflow = compile_grocery_workflow()
    for n in [2, 4, 5]:
        state = {
            "query": "basket test",
            "category": "grocery",
            "items": queries[:n],
            "objective": "balanced",
            "route": "direct-basket",
            "mcp_tools_used": [],
            "mcp_results": [],
            "evidence": [],
            "reasoning": [],
            "response": {},
            "observability": []
        }
        res = await workflow.ainvoke(state)
        rec = res.get("recommended_basket")
        print(f"\nBasket ({n} items): recommended={rec.provider if rec else None}, items={len(rec.items) if rec else 0}")
        if rec:
            for item in rec.items:
                print("  item:", item.provider, item.title, item.price)

asyncio.run(main())
