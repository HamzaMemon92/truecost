import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()
from app.providers.quickcommerce_provider import QuickCommerceProvider, _QC_PLATFORMS, _QC_BASE_URL
from app.config import settings
import httpx

async def main():
    headers = {
        "X-API-Key": settings.quickcommerce_api_key,
        "Accept": "application/json",
    }
    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(
            f"{_QC_BASE_URL}/search",
            params={"q": "milk", "platform": "BlinkIt", "lat": settings.quickcommerce_lat, "lon": settings.quickcommerce_lon},
            timeout=10,
        )
        data = resp.json()
        # Print full structure of first 2 products
        products = data.get("data", {}).get("products") or data.get("products") or []
        print(f"Top-level keys: {list(data.keys())}")
        print(f"data keys: {list(data.get('data', {}).keys()) if 'data' in data else 'N/A'}")
        print(f"Total products: {len(products)}")
        if products:
            print("\nFIRST PRODUCT (full):")
            print(json.dumps(products[0], indent=2, default=str))
            if len(products) > 1:
                print("\nSECOND PRODUCT (full):")
                print(json.dumps(products[1], indent=2, default=str))

asyncio.run(main())
