import asyncio
import httpx
import json
import os

async def test_api():
    api_key = "7c5a2a5d-114a-4106-9f72-4ce67de5deb3"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.quickcommerceapi.com/v1/groupsearch",
            params={
                "q": "Amul Butter 500g",
                "platforms": "blinkit,zepto,swiggy",
                "lat": "12.9716",
                "lon": "77.5946"
            },
            headers={"X-API-Key": api_key, "Accept": "application/json"}
        )
        print("Status code:", resp.status_code)
        
        with open("qc_groupsearch.json", "w", encoding="utf-8") as f:
            json.dump(resp.json(), f, indent=2)

if __name__ == "__main__":
    asyncio.run(test_api())
