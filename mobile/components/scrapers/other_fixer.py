import os
import re

def fix_scraper(filepath, new_source_template, extra_fallback=""):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove isReady state
    content = re.sub(r'const \[isReady, setIsReady\] = React\.useState\(false\);\n?', '', content)
    # Remove useEffect navigation
    content = re.sub(r'useEffect\(\(\) => \{[\s\S]*?\}, \[query, isReady\]\);\n?', '', content)
    content = re.sub(r'useEffect\(\(\) => \{[\s\S]*?\}, \[query\]\);\n?', '', content)
    # Remove onLoad
    content = re.sub(r'onLoad=\{\(\) => \{ setIsReady\(true\); \}\}', '', content)
    
    # Add handleLoadEnd if not exists and inject FALLBACK_INJECT
    if extra_fallback and 'handleLoadEnd' not in content:
        on_message_idx = content.find('const onMessage = (event: any) => {')
        handle_load_str = "\n  const handleLoadEnd = () => {\n    if (query) webViewRef.current?.injectJavaScript(FALLBACK_INJECT);\n  };\n\n"
        content = content[:on_message_idx] + handle_load_str + content[on_message_idx:]
        
        # Add onLoadEnd to WebView
        content = content.replace('onMessage={onMessage}', 'onMessage={onMessage}\n        onLoadEnd={handleLoadEnd}')

    # Inject FALLBACK_INJECT constant before component definition
    if extra_fallback and 'FALLBACK_INJECT = `' not in content:
        comp_def_idx = content.find('export default function')
        content = content[:comp_def_idx] + extra_fallback + "\n\n" + content[comp_def_idx:]
    
    # Replace source
    content = re.sub(r'source=\{\{\s*uri:\s*[^}]+\s*\}\}', 'source={{' + new_source_template + '}}', content)

    # Clean up imports
    content = content.replace('import React, { useRef, useEffect }', 'import React, { useRef }')
    content = content.replace('import React, { useRef, useState, useEffect }', 'import React, { useRef }')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

base_dir = r"C:\Users\Mohammad Anas\Downloads\decision-advisor-main\decision-advisor-main\mobile\components\scrapers\\"

# Pharmacy Fallbacks
tata_fallback = """const FALLBACK_INJECT = `
  (function() {
    function extract() {
      try {
        const cards = document.querySelectorAll('[data-testid="product-card"], [class*="ProductCard"]');
        if (cards && cards.length > 0) {
          let items = [];
          cards.forEach(c => {
            const titleEl = c.querySelector('h2, h3, [class*="name"]');
            const priceEl = c.querySelector('[class*="Price"]');
            if (titleEl && priceEl) {
              items.push({
                name: titleEl.textContent.trim(),
                selling_price: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10),
                mrp: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10),
                thumbnail: '',
                url_key: titleEl.textContent.trim()
              });
            }
          });
          if (items.length > 0) {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: { products: items } }));
          }
        }
      } catch(e) {}
    }
    setTimeout(extract, 2000);
  })();
  true;
`;"""

pharmeasy_fallback = """const FALLBACK_INJECT = `
  (function() {
    function extract() {
      try {
        const cards = document.querySelectorAll('[class*="ProductCard"], [class*="medicinecard"]');
        if (cards && cards.length > 0) {
          let items = [];
          cards.forEach(c => {
            const titleEl = c.querySelector('h1, h2, h3');
            const priceEl = c.querySelector('[class*="price"]');
            if (titleEl && priceEl) {
              items.push({
                name: titleEl.textContent.trim(),
                discounted_price: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10),
                mrp: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10),
                image_url: '',
                slug: titleEl.textContent.trim()
              });
            }
          });
          if (items.length > 0) {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: { products: items } }));
          }
        }
      } catch(e) {}
    }
    setTimeout(extract, 2000);
  })();
  true;
`;"""

apollo_fallback = """const FALLBACK_INJECT = `
  (function() {
    function extract() {
      try {
        const cards = document.querySelectorAll('[data-testid="product"], [class*="productCard"]');
        if (cards && cards.length > 0) {
          let items = [];
          cards.forEach(c => {
            const titleEl = c.querySelector('h2, h3, p');
            const priceEl = c.querySelector('[class*="price"]');
            if (titleEl && priceEl) {
              items.push({
                name: titleEl.textContent.trim(),
                price: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10),
                mrp: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10),
                imageUrl: '',
                productUrl: ''
              });
            }
          });
          if (items.length > 0) {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: { products: items } }));
          }
        }
      } catch(e) {}
    }
    setTimeout(extract, 2000);
  })();
  true;
`;"""

netmeds_fallback = """const FALLBACK_INJECT = `
  (function() {
    function extract() {
      try {
        const cards = document.querySelectorAll('[class*="cat-product-box"], [class*="prod-name"]');
        if (cards && cards.length > 0) {
          let items = [];
          cards.forEach(c => {
            const titleEl = c.querySelector('h3, [class*="name"]');
            const priceEl = c.querySelector('[class*="price"]');
            if (titleEl && priceEl) {
              items.push({
                name: titleEl.textContent.trim(),
                selling_price: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10),
                mrp: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10),
                image: '',
                sku_id: titleEl.textContent.trim()
              });
            }
          });
          if (items.length > 0) {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: { products: items } }));
          }
        }
      } catch(e) {}
    }
    setTimeout(extract, 2000);
  })();
  true;
`;"""


# Pharmacy
pharmacy_dir = base_dir + "pharmacy\\"
fix_scraper(pharmacy_dir + "Tata1mgScraper.tsx", "uri: query ? `https://www.1mg.com/search/all?name=${encodeURIComponent(query)}` : 'https://www.1mg.com/'", tata_fallback)
fix_scraper(pharmacy_dir + "PharmEasyScraper.tsx", "uri: query ? `https://pharmeasy.in/search/all?name=${encodeURIComponent(query)}` : 'https://pharmeasy.in/'", pharmeasy_fallback)
fix_scraper(pharmacy_dir + "Apollo247Scraper.tsx", "uri: query ? `https://www.apollo247.com/search?query=${encodeURIComponent(query)}` : 'https://www.apollo247.com/'", apollo_fallback)
fix_scraper(pharmacy_dir + "NetmedsScraper.tsx", "uri: query ? `https://www.netmeds.com/catalogsearch/result?q=${encodeURIComponent(query)}` : 'https://www.netmeds.com/'", netmeds_fallback)

# Travel
travel_dir = base_dir + "travel\\"
fix_scraper(travel_dir + "MakeMyTripScraper.tsx", "uri: query ? `https://www.makemytrip.com/flights/search?q=${encodeURIComponent(query)}` : 'https://www.makemytrip.com/flights/'")
fix_scraper(travel_dir + "GoibiboScraper.tsx", "uri: query ? `https://www.goibibo.com/flights/search?q=${encodeURIComponent(query)}` : 'https://www.goibibo.com/flights/'")
fix_scraper(travel_dir + "IxigoScraper.tsx", "uri: query ? `https://www.ixigo.com/search/result/flight?q=${encodeURIComponent(query)}` : 'https://www.ixigo.com/flights'")
fix_scraper(travel_dir + "CleartripScraper.tsx", "uri: query ? `https://www.cleartrip.com/flights/results?q=${encodeURIComponent(query)}` : 'https://www.cleartrip.com/'")

# Finance
finance_dir = base_dir + "finance\\"
fix_scraper(finance_dir + "BankBazaarScraper.tsx", "uri: query ? `https://www.bankbazaar.com/search.html?q=${encodeURIComponent(query)}` : 'https://www.bankbazaar.com/'")
fix_scraper(finance_dir + "PolicyBazaarScraper.tsx", "uri: query ? `https://www.policybazaar.com/search/?q=${encodeURIComponent(query)}` : 'https://www.policybazaar.com/'")
fix_scraper(finance_dir + "PaisaBazaarScraper.tsx", "uri: query ? `https://www.paisabazaar.com/search/?q=${encodeURIComponent(query)}` : 'https://www.paisabazaar.com/'")
fix_scraper(finance_dir + "CreditMantriScraper.tsx", "uri: query ? `https://www.creditmantri.com/credit-cards/?q=${encodeURIComponent(query)}` : 'https://www.creditmantri.com/'")

# Productivity
prod_dir = base_dir + "productivity\\"
fix_scraper(prod_dir + "NotionScraper.tsx", "uri: 'https://www.notion.so/pricing'")
fix_scraper(prod_dir + "FigmaScraper.tsx", "uri: 'https://www.figma.com/pricing/'")
fix_scraper(prod_dir + "SlackScraper.tsx", "uri: 'https://slack.com/intl/en-in/pricing'")
fix_scraper(prod_dir + "CanvaScraper.tsx", "uri: 'https://www.canva.com/pricing/'")

print("All others Done!")
