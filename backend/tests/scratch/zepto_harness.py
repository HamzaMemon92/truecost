import httpx
import json
import asyncio

async def test_zepto_endpoint():
    url = "https://bff-gateway.zepto.com/user-search-service/api/v3/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Plausible payload based on context
    payload = {
        "query": "Amul milk",
        "pageNumber": 1,
        "mode": "SEARCH"
    }
    
    print(f"Testing {url} without auth/session tokens...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=10.0)
            print(f"Status Code: {resp.status_code}")
            print(f"Headers: {dict(resp.headers)}")
            try:
                print(f"JSON Response: {json.dumps(resp.json(), indent=2)}")
            except Exception:
                print(f"Text Response: {resp.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_zepto_endpoint())
