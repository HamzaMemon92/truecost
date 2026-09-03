import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import asyncio
import json
import traceback
from app.api.endpoints.aggregator import ingest_scraped_data, IngestPayload
from app.db import get_db
from app.graph.grocery_workflow import compile_grocery_workflow

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
        
    workflow = compile_grocery_workflow()
    common_queries = ["Red Bull", "Thums Up", "Nutella", "Oreo", "Dairy Milk"]
    for n in [2, 4, 5]:
        state = {
            "query": "test query",
            "category": "grocery",
            "session_id": None,
            "user_id": None,
            "preferences": {},
            "items": common_queries[:n],
            "objective": "balanced",
            "constraints": {},
            "context": {},
            "route": "direct-basket",
            "complexity": "simple",
            "agent_type": "None",
            "mcp_tools_used": [],
            "mcp_results": [],
            "evidence": [],
            "provider_results": [],
            "basket_results": [],
            "product_comparisons": [],
            "recommended_basket": None,
            "alternative_baskets": [],
            "substitutions": [],
            "provider_warnings": [],
            "payment_benefits": [],
            "verification": [],
            "reasoning": [],
            "response": {},
            "observability": []
        }
        try:
            res_state = await workflow.ainvoke(state)
            rec = res_state.get("recommended_basket")
            print(f"n={n}: rec={rec.provider if rec else None}, items={len(rec.items) if rec else 0}")
        except Exception:
            traceback.print_exc()

asyncio.run(main())
