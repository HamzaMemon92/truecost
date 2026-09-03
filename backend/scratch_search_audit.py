import asyncio
from pprint import pprint
from app.providers.mock_grocery_provider import MockFastGroceryProvider
from app.schemas.grocery import Location

async def run_audit():
    queries = [
        "milk", "bread", "eggs", "coffee", "rice",
        "amul taaza toned milk 1 litre", "amul taaza 500 ml", "full cream milk 1 litre", "6 eggs", "12 eggs", "britannia whole wheat bread",
        "mil", "milkk", "brd", "amul1l", "milk 1000ml", "milk 1 litre 50 rupees", "2x milk",
        "I need 1 litre toned milk", "give me cheap amul milk", "find milk under 60", "I want two 1 litre packs of milk"
    ]
    
    provider = MockFastGroceryProvider()
    location = Location(postal_code="110001")
    
    print("SEARCH ADVERSARIAL TESTING RESULTS")
    for q in queries:
        print(f"\n--- Query: {q} ---")
        try:
            results = await provider.search(q, location)
            print(f"Found {len(results)} results")
            for r in results[:2]:
                print(f" - {r.get('title', 'Unknown')} ({r.get('canonical_product_id', 'none')}) - Price: {r.get('price')} - Avail: {r.get('availability')}")
        except Exception as e:
            print(f"ERROR: {e}")

asyncio.run(run_audit())
