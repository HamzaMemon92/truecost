import os

def fix_scraper(filepath, original_source_regex, new_source_template, extra_fallback):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    import re
    # Remove isReady state
    content = re.sub(r'const \[isReady, setIsReady\] = React\.useState\(false\);\n?', '', content)
    # Remove useEffect navigation
    content = re.sub(r'useEffect\(\(\) => \{[\s\S]*?\}, \[query, isReady\]\);\n?', '', content)
    # Remove onLoad
    content = re.sub(r'onLoad=\{\(\) => \{ setIsReady\(true\); \}\}', '', content)
    
    # Add handleLoadEnd if not exists and inject FALLBACK_INJECT
    if 'handleLoadEnd' not in content:
        on_message_idx = content.find('const onMessage = (event: any) => {')
        handle_load_str = "\n  const handleLoadEnd = () => {\n    if (query) webViewRef.current?.injectJavaScript(FALLBACK_INJECT);\n  };\n\n"
        content = content[:on_message_idx] + handle_load_str + content[on_message_idx:]
        
        # Add onLoadEnd to WebView
        content = content.replace('onMessage={onMessage}', 'onMessage={onMessage}\n        onLoadEnd={handleLoadEnd}')

    # Inject FALLBACK_INJECT constant before component definition
    if 'FALLBACK_INJECT = `' not in content:
        comp_def_idx = content.find('export default function')
        content = content[:comp_def_idx] + extra_fallback + "\n\n" + content[comp_def_idx:]

    # Replace source
    content = re.sub(r'source=\{\{\s*uri:\s*[^}]+\s*\}\}', 'source={{' + new_source_template + '}}', content)

    # Clean up imports
    content = content.replace('import React, { useRef, useEffect }', 'import React, { useRef }')
    content = content.replace('import React, { useRef, useState, useEffect }', 'import React, { useRef }')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


grocery_dir = r"C:\Users\Mohammad Anas\Downloads\decision-advisor-main\decision-advisor-main\mobile\components\scrapers\grocery\\"
food_dir = r"C:\Users\Mohammad Anas\Downloads\decision-advisor-main\decision-advisor-main\mobile\components\scrapers\food\\"

# --- GROCERY ---
zepto_fallback = """const FALLBACK_INJECT = `
  (function() {
    function extract() {
      try {
        const cards = document.querySelectorAll('[class*="ProductCard"], [data-testid*="product"], .css-');
        if (cards && cards.length > 0) {
          let items = [];
          cards.forEach(c => {
            const titleEl = c.querySelector('h5, h4, p, [class*="title"]');
            const priceEl = c.querySelector('[class*="price"], h4');
            const imgEl = c.querySelector('img');
            if (titleEl && priceEl) {
              const title = titleEl.textContent.trim();
              const price = parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10);
              if (title && price > 0) {
                items.push({
                  name: title,
                  sp: price,
                  mrp: price,
                  img_url: imgEl ? imgEl.src : '',
                  nav_id: title
                });
              }
            }
          });
          if (items.length > 0) {
            window.ReactNativeWebView.postMessage(JSON.stringify({
              type: 'SEARCH_SUCCESS',
              payload: { products: items }
            }));
            return true;
          }
        }
      } catch(e) {}
      return false;
    }
    if (!extract()) {
      setTimeout(extract, 1500);
      setTimeout(extract, 3000);
    }
  })();
  true;
`;"""
fix_scraper(
    grocery_dir + "ZeptoScraper.tsx",
    "",
    "uri: query ? `https://www.zeptonow.com/search?query=${encodeURIComponent(query)}` : 'https://www.zeptonow.com/'",
    zepto_fallback
)

blinkit_fallback = """const FALLBACK_INJECT = `
  (function() {
    function extract() {
      try {
        const cards = document.querySelectorAll('[data-test-id="product-card"], [class*="Product"]');
        if (cards && cards.length > 0) {
          let items = [];
          cards.forEach(c => {
            const titleEl = c.querySelector('[class*="name"], [class*="Title"]');
            const priceEl = c.querySelector('[class*="price"], div:contains("₹")');
            if (titleEl && priceEl) {
              items.push({
                name: titleEl.textContent.trim(),
                sp: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10),
                mrp: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10),
                img_url: '',
                nav_id: titleEl.textContent.trim()
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
fix_scraper(
    grocery_dir + "BlinkitScraper.tsx",
    "",
    "uri: query ? `https://blinkit.com/s/?q=${encodeURIComponent(query)}` : 'https://blinkit.com/'",
    blinkit_fallback
)

swiggy_fallback = """const FALLBACK_INJECT = `
  (function() {
    function extract() {
      try {
        const cards = document.querySelectorAll('[data-testid*="item"], [class*="ItemCard"]');
        if (cards && cards.length > 0) {
          let items = [];
          cards.forEach(c => {
            const titleEl = c.querySelector('[class*="name"]');
            const priceEl = c.querySelector('[class*="price"]');
            if (titleEl && priceEl) {
              items.push({
                name: titleEl.textContent.trim(),
                sp: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10),
                mrp: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10),
                img_url: ''
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
fix_scraper(
    grocery_dir + "SwiggyInstamartScraper.tsx",
    "",
    "uri: query ? `https://www.swiggy.com/instamart/search?custom_back=true&query=${encodeURIComponent(query)}` : 'https://www.swiggy.com/instamart'",
    swiggy_fallback
)

bb_fallback = """const FALLBACK_INJECT = `
  (function() {
    function extract() {
      try {
        if (window.__PRELOADED_STATE__) {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: window.__PRELOADED_STATE__ }));
            return;
        }
        const cards = document.querySelectorAll('[qa="product-section"], [class*="SKUDeck"]');
        if (cards && cards.length > 0) {
          let items = [];
          cards.forEach(c => {
            const titleEl = c.querySelector('[class*="prod-name"]');
            const priceEl = c.querySelector('[class*="Price"]');
            if (titleEl && priceEl) {
              items.push({
                desc: titleEl.textContent.trim(),
                aps: { sp: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10), mrp: parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10) },
                ib: { m: '' },
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
fix_scraper(
    grocery_dir + "BigBasketScraper.tsx",
    "",
    "uri: query ? `https://www.bigbasket.com/ps/?q=${encodeURIComponent(query)}&nc=as` : 'https://www.bigbasket.com/'",
    bb_fallback
)

print("Grocery Done!")
