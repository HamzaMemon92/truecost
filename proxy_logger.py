from fastapi import FastAPI, Request, Response
import uvicorn
import httpx
import json
from datetime import datetime, timezone

app = FastAPI()

@app.post("/api/v1/aggregator/ingest")
async def proxy_ingest(request: Request):
    body = await request.body()
    data = await request.json()
    
    capture = {
        "capture_version": "1.0",
        "run_id": "debug_run_5",
        "case_id": "grocery_exact_known_product",
        "domain": "grocery",
        "provider": data.get("provider"),
        "query": data.get("query"),
        "execution_mode": "REAL_LIVE_SCRAPE",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "message_type": "SEARCH_SUCCESS",
        "scraper_component": "BlinkitScraper",
        "payload": data.get("raw_data")
    }
    
    with open("capture_blinkit_live.json", "w", encoding="utf-8") as f:
        json.dump(capture, f, indent=2)
        
    print("SAVED CAPTURE to capture_blinkit_live.json")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post("http://127.0.0.1:8000/api/v1/aggregator/ingest", content=body, headers={"Content-Type": "application/json"})
        return Response(content=resp.content, status_code=resp.status_code)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
