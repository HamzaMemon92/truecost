import httpx

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

try:
    with httpx.Client(headers=headers, follow_redirects=True, timeout=10.0) as client:
        r = client.get('https://www.swiggy.com/instamart')
        print(f"Status: {r.status_code}")
        print(f"Final URL: {r.url}")
        print(f"Response snippet: {r.text[:300]}")
        
        # Also try search API
        api_headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.swiggy.com/instamart',
        }
        r2 = client.get('https://www.swiggy.com/api/instamart/search/v2?offset=0&query=milk', headers=api_headers)
        print(f"\nAPI Status: {r2.status_code}")
        print(f"API Response snippet: {r2.text[:300]}")
except Exception as e:
    print(f"Error: {e}")
