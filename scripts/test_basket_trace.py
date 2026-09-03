import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import asyncio
import json
from app.api.endpoints.aggregator import ingest_scraped_data, IngestPayload
from app.db import get_db
from app.mcp.grocery_client import GroceryMcpClient
from app.graph.grocery_basket_engine import BasketBuilder, CostCalculator, ConstraintEngine, BasketOptimizer
from app.schemas.grocery import CanonicalGroceryItem

class MockResponse:
    status_code = 200
    def __init__(self):
        self.headers = {}

async def main():
    MATRIX_DIR = "backend/tests/fixtures/scraper_certification/runs/MATRIX"
    files = sorted([f for f in os.listdir(MATRIX_DIR) if "common" in f and f.endswith(".json")])
    for file in files:
        path = os.path.join(MATRIX_DIR, file)
        with open(path, "r", encoding="utf-8") as f:
            capture = json.load(f)
        payload = IngestPayload(
            provider=capture["provider"],
            query=capture.get("query", "Unknown"),
            location="default",
            category="Grocery",
            raw_data=capture["payload"]
        )
        db = next(get_db())
        await ingest_scraped_data(payload=payload, response=MockResponse(), db=db, credentials=None)
        
    mcp_client = GroceryMcpClient()
    queries = ["Red Bull", "Thums Up", "Nutella", "Oreo", "Dairy Milk"]
    
    for n in [2, 4, 5]:
        sub_queries = queries[:n]
        print(f"\n--- Testing for n={n} queries: {sub_queries} ---")
        all_items = []
        for q in sub_queries:
            res = await mcp_client.call_tool("search_items", {"query": q})
            items = res.get("items", [])
            print(f"Query '{q}' returned {len(items)} items")
            for it in items:
                if it.get("er_decision") != "REJECTED":
                    all_items.append(CanonicalGroceryItem(**it))
                    
        print(f"Total non-rejected canonical items: {len(all_items)}")
        baskets = BasketBuilder.build(all_items)
        print(f"Baskets built: {len(baskets)}")
        for b in baskets:
            print(f"  {b.provider}: {len(b.items)} items")
            
        baskets = CostCalculator.calculate_all(baskets)
        baskets = ConstraintEngine.evaluate_all(baskets, sub_queries)
        for b in baskets:
            print(f"  {b.provider}: missing={b.missing_items}, subtotal={b.subtotal}, final_total={b.final_total}")
            
        ranked = BasketOptimizer.optimize(baskets, "balanced")
        print(f"Ranked baskets: {len(ranked)}")
        if ranked:
            print(f"Recommended: {ranked[0].provider}, items={len(ranked[0].items)}")
        else:
            print("No recommended basket!")

asyncio.run(main())
