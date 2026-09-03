import os
import re

providers = [
    {"id": "namma_yatri", "class_name": "NammaYatri", "cat": "Mobility", "url": "https://nammayatri.in/", "name": "Namma Yatri"},
    {"id": "meesho", "class_name": "Meesho", "cat": "Shopping", "url": "https://www.meesho.com/", "name": "Meesho"},
    {"id": "myntra", "class_name": "Myntra", "cat": "Shopping", "url": "https://www.myntra.com/", "name": "Myntra"},
    {"id": "magicpin", "class_name": "MagicPin", "cat": "Food", "url": "https://magicpin.in/", "name": "MagicPin"},
    {"id": "eatsure", "class_name": "EatSure", "cat": "Food", "url": "https://www.eatsure.com/", "name": "EatSure"},
    {"id": "apollo247", "class_name": "Apollo247", "cat": "Pharmacy", "url": "https://www.apollo247.com/", "name": "Apollo 247"},
    {"id": "netmeds", "class_name": "Netmeds", "cat": "Pharmacy", "url": "https://www.netmeds.com/", "name": "Netmeds"},
    {"id": "ixigo", "class_name": "Ixigo", "cat": "Travel", "url": "https://www.ixigo.com/", "name": "Ixigo"},
    {"id": "cleartrip", "class_name": "Cleartrip", "cat": "Travel", "url": "https://www.cleartrip.com/", "name": "Cleartrip"},
    {"id": "policybazaar", "class_name": "PolicyBazaar", "cat": "Finance", "url": "https://www.policybazaar.com/", "name": "PolicyBazaar"},
    {"id": "paisabazaar", "class_name": "PaisaBazaar", "cat": "Finance", "url": "https://www.paisabazaar.com/", "name": "PaisaBazaar"},
    {"id": "creditmantri", "class_name": "CreditMantri", "cat": "Finance", "url": "https://www.creditmantri.com/", "name": "CreditMantri"},
    {"id": "slack", "class_name": "Slack", "cat": "Productivity", "url": "https://slack.com/intl/en-in/pricing", "name": "Slack"},
    {"id": "canva", "class_name": "Canva", "cat": "Productivity", "url": "https://www.canva.com/pricing/", "name": "Canva"},
]

def make_connector(p):
    return f"""from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice

class {p["class_name"]}Connector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "{p['name']}"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            items = raw_payload.get("items", [])
            for item in items:
                price = float(item.get("price", 0))
                orig = item.get("original_price")
                orig = float(orig) if orig else None
                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=orig,
                    delivery_time=item.get("delivery_time", "Standard"),
                    deep_link=item.get("link", "{p['url']}")
                )
                tc_product = TrueCostProduct(
                    id=f"tc_{p['id']}_{{item.get('name', 'product').replace(' ', '_').lower()}}",
                    name=item.get("name", "{p['name']} Product"),
                    brand="{p['name']}",
                    weight_volume="",
                    image_url=item.get("image_url", ""),
                    category="{p['cat']}",
                    prices=[provider_price]
                )
                products.append(tc_product)
        except Exception as e:
            print(f"[{p['class_name']}Connector] Error: {{e}}")
        return products
"""

def make_scraper(p):
    cat_lower = p['cat'].lower()
    return f"""import React, {{ useRef, useEffect }} from 'react';
import {{ View, StyleSheet }} from 'react-native';
import {{ WebView }} from 'react-native-webview';

interface ScraperProps {{
  query: string;
  onResults: (data: any) => void;
  onError: (error: string) => void;
  latitude?: number;
  longitude?: number;
}}

const INJECT_SCRIPT = `
  (function() {{
    function extractData() {{
      // Generic fallback extractor
      const items = [];
      document.querySelectorAll('h2, h3, .price, .amount, .title, .product, .card, [class*="product"], [class*="card"], [class*="price"]').forEach(el => {{
        const text = el.textContent || '';
        if (text.includes('₹') || /[0-9]+/.test(text)) {{
            const priceMatch = text.match(/₹?\\s*([0-9,.]+)/);
            if(priceMatch && priceMatch[1]) {{
                 items.push({{
                    name: "Search Result", 
                    price: parseFloat(priceMatch[1].replace(/,/g, '')),
                    delivery_time: "{p['cat'] == 'Food' or p['cat'] == 'Grocery' and '30 mins' or '2-3 Days'}",
                 }});
            }}
        }}
      }});
      if (items.length > 0) {{
        window.ReactNativeWebView.postMessage(JSON.stringify({{ type: 'SEARCH_SUCCESS', payload: {{ items: items.slice(0, 5) }} }}));
      }}
    }}
    setTimeout(extractData, 3000);
  }})();
  true;
`;

export default function {p['class_name']}Scraper({{ query, onResults, onError }}: ScraperProps) {{
  const webViewRef = useRef<WebView>(null);
  const isReady = useRef(false);

  useEffect(() => {{
    if (isReady.current && query) {{
      const searchUrl = '{p['url']}';
      webViewRef.current?.injectJavaScript(`window.location.href = '${{searchUrl}}'; true;`);
      setTimeout(() => {{
          webViewRef.current?.injectJavaScript(INJECT_SCRIPT);
      }}, 3000);
    }}
  }}, [query]);

  const onMessage = (event: any) => {{
    try {{
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'SEARCH_SUCCESS') onResults(data.payload);
      else if (data.type === 'SEARCH_ERROR') onError(data.message);
    }} catch (_) {{}}
  }};

  return (
    <View style={{styles.c}}>
      <WebView ref={{webViewRef}} source={{{{ uri: '{p['url']}' }}}}
        onMessage={{onMessage}} onLoad={{() => {{ isReady.current = true; }}}}
        javaScriptEnabled domStorageEnabled style={{styles.h}}
        userAgent="Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/116.0.0.0 Mobile Safari/537.36"
      />
    </View>
  );
}}

const styles = StyleSheet.create({{
  c: {{ width: 0, height: 0, position: 'absolute', opacity: 0 }},
  h: {{ width: 0, height: 0, opacity: 0 }},
}});
"""

# Write all connectors and scrapers
for p in providers:
    conn_path = f"backend/app/connectors/{p['id']}.py"
    with open(conn_path, "w", encoding="utf-8") as f:
        f.write(make_connector(p))
    
    cat_dir = f"mobile/components/scrapers/{p['cat'].lower()}"
    os.makedirs(cat_dir, exist_ok=True)
    scrap_path = f"{cat_dir}/{p['class_name']}Scraper.tsx"
    with open(scrap_path, "w", encoding="utf-8") as f:
        f.write(make_scraper(p))

print("Scrapers and Connectors generated.")
