import React, { useEffect, useRef } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

interface ScraperProps {
  query: string;
  latitude?: number;
  longitude?: number;
  onResults: (data: any) => void;
  onError: (error: string) => void;
}

const FALLBACK_INJECT = `
  (function() {
    const PRICE_RE = /(?:Rs\\.?|INR|₹)\\s*([0-9]+(?:\\.[0-9]+)?)/i;
    function cleanText(value) {
      return String(value || '').replace(/\\s+/g, ' ').trim();
    }
    function firstPrice(text) {
      const match = cleanText(text).match(PRICE_RE);
      return match ? Number(match[1]) : null;
    }
    function titleFromCard(card, text) {
      const preferred = card.querySelector('[data-testid*="name"], [class*="name"], [class*="Name"], [class*="title"], [class*="Title"], h1, h2, h3, h4');
      const preferredText = cleanText(preferred && preferred.textContent);
      if (preferredText && !PRICE_RE.test(preferredText) && preferredText.length <= 140) return preferredText;
      return cleanText(text).split(/(?=\\b[A-Z][a-z])/).find(part => {
        const value = cleanText(part);
        return value.length >= 4 && value.length <= 140 && !PRICE_RE.test(value);
      }) || '';
    }
    function extract() {
      try {
        const cards = document.querySelectorAll([
          '[data-testid*="item"]',
          '[data-testid*="product"]',
          '[class*="ItemCard"]',
          '[class*="Product"]',
          '[class*="product"]',
          'a[href*="/instamart"]',
          'a[href*="/product"]'
        ].join(', '));
        if (cards && cards.length > 0) {
          let items = [];
          cards.forEach(c => {
            const text = cleanText(c.textContent);
            const name = titleFromCard(c, text);
            const price = firstPrice(text);
            if (name && price && price > 0 && price < 100000) {
              const imgEl = c.querySelector('img');
              const linkEl = c.closest('a[href]') || c.querySelector('a[href]');
              items.push({
                name,
                sp: price,
                mrp: price,
                img_url: imgEl ? imgEl.src : '',
                url: linkEl ? linkEl.href : ''
              });
            }
          });
          const seen = {};
          items = items.filter(item => {
            const key = (item.name + '|' + item.sp).toLowerCase();
            if (seen[key]) return false;
            seen[key] = true;
            return true;
          }).slice(0, 40);
          if (items.length > 0) {
            window.__truecostSwiggySent = true;
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: { products: items } }));
            return true;
          }
        }
      } catch(e) {
        window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Fallback extract failed: ' + e.message }));
      }
      return false;
    }
    if (!extract()) {
      setTimeout(extract, 2000);
      setTimeout(extract, 5000);
      setTimeout(extract, 9000);
    }
  })();
  true;
`;

const RESILIENT_FALLBACK_INJECT = `
  (function() {
    const PRICE_RE = /(?:\\u20b9|Rs\\.?|INR)\\s*([0-9]+(?:\\.[0-9]+)?)/i;
    const SIZE_RE = /\\b\\d+(?:\\.\\d+)?\\s*(?:ml|l|lt|ltr|litre|liter|g|kg|pc|pcs|pack)\\b(?:\\s*x\\s*\\d+)?/i;
    function cleanText(value) {
      return String(value || '').replace(/\\s+/g, ' ').trim();
    }
    function firstPrice(text) {
      const match = cleanText(text).match(PRICE_RE);
      return match ? Number(match[1]) : null;
    }
    function firstSize(text) {
      const match = cleanText(text).match(SIZE_RE);
      return match ? match[0] : '';
    }
    function imageSrc(img) {
      if (!img) return '';
      const srcset = img.getAttribute('srcset') || '';
      const fromSrcset = srcset.split(',').map(part => part.trim().split(/\\s+/)[0]).find(Boolean);
      return img.currentSrc || img.src || fromSrcset || '';
    }
    function titleFromCard(card, text) {
      const preferred = card.querySelector('[data-testid*="name"], [data-testid*="title"], [class*="name"], [class*="Name"], [class*="title"], [class*="Title"], [aria-label], h1, h2, h3, h4');
      const preferredText = cleanText(preferred && (preferred.textContent || preferred.getAttribute('aria-label')));
      if (preferredText && !PRICE_RE.test(preferredText) && preferredText.length <= 140) return preferredText;
      const aria = cleanText(card.getAttribute('aria-label') || card.getAttribute('title') || '');
      if (aria && !PRICE_RE.test(aria) && aria.length <= 140) return aria;
      return cleanText(text).split(/(?=\\b[A-Z][a-z])|\\u20b9|Rs\\.?/i).find(part => {
        const value = cleanText(part);
        return value.length >= 4 && value.length <= 140 && !PRICE_RE.test(value);
      }) || '';
    }
    function productAncestor(node) {
      let current = node;
      let depth = 0;
      while (current && depth < 8) {
        const text = cleanText(current.textContent);
        if (PRICE_RE.test(text) && text.length > 12 && text.length < 900) return current;
        current = current.parentElement;
        depth += 1;
      }
      return node;
    }
    function priceFromNode(node) {
      if (!node || typeof node !== 'object') return null;
      const direct = node.sp || node.sellingPrice || node.offerPrice || node.offer_price || node.finalPrice || node.price;
      if (typeof direct === 'number') return direct > 999 ? direct / 100 : direct;
      if (direct && typeof direct === 'object') {
        const value = direct.offerPrice || direct.offer_price || direct.finalPrice || direct.sellingPrice || direct.price || direct.sp || direct.mrp || direct.units;
        if (typeof value === 'number') return value > 999 ? value / 100 : value;
        if (value && typeof value === 'object' && typeof value.units === 'number') return value.units > 999 ? value.units / 100 : value.units;
      }
      return null;
    }
    function imageFromNode(node) {
      if (!node || typeof node !== 'object') return '';
      const direct = node.imageUrl || node.image_url || node.img_url || node.image || node.thumbnail || node.imageId;
      if (typeof direct === 'string') return direct;
      const ids = node.imageIds || node.images || node.media;
      if (Array.isArray(ids) && ids.length) {
        const first = ids[0];
        if (typeof first === 'string') return first;
        if (first && typeof first === 'object') return first.url || first.imageUrl || first.image_url || first.id || '';
      }
      return '';
    }
    function collectJsonProducts(root) {
      const out = [];
      const seen = new Set();
      function walk(node) {
        if (!node || out.length >= 40) return;
        if (Array.isArray(node)) {
          node.forEach(walk);
          return;
        }
        if (typeof node !== 'object') return;
        const name = node.displayName || node.productName || node.product_name || node.name || node.title;
        const price = priceFromNode(node);
        if (name && price && price > 0 && price < 100000) {
          const unit = node.quantityDescription || node.quantity || node.unit || node.weight || node.packSize || firstSize(JSON.stringify(node).slice(0, 1000)) || '1 unit';
          const id = node.skuId || node.sku_id || node.productId || node.product_id || node.id || name;
          const key = String(id + '|' + name + '|' + unit + '|' + price).toLowerCase();
          if (!seen.has(key)) {
            seen.add(key);
            out.push({
              id,
              skuId: node.skuId || node.sku_id || id,
              name: String(name),
              brand: node.brandName || node.brand || '',
              sp: price,
              mrp: priceFromNode({ price: node.mrp || node.maxPrice }) || price,
              unit,
              img_url: imageFromNode(node),
              url: node.productUrl || node.url || ''
            });
          }
        }
        Object.keys(node).forEach(key => walk(node[key]));
      }
      walk(root);
      return out;
    }
    function extractStructuredState() {
      try {
        const next = document.querySelector('script#__NEXT_DATA__');
        if (next && next.textContent) {
          const products = collectJsonProducts(JSON.parse(next.textContent));
          if (products.length) return products;
        }
      } catch(e) {
        window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Structured extract failed: ' + e.message }));
      }
      return [];
    }
    function extract() {
      try {
        const structured = extractStructuredState();
        if (structured.length > 0) {
          window.__truecostSwiggySent = true;
          window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: { products: structured } }));
          return true;
        }
        const nodes = Array.from(document.querySelectorAll([
          '[data-testid*="item"]',
          '[data-testid*="product"]',
          '[class*="ItemCard"]',
          '[class*="Product"]',
          '[class*="product"]',
          '[role="listitem"]',
          'a[href*="/instamart"]',
          'a[href*="/product"]',
          'img'
        ].join(', '))).map(productAncestor);
        let items = [];
        nodes.forEach(card => {
          const text = cleanText(card.textContent);
          const price = firstPrice(text);
          const name = titleFromCard(card, text);
          if (!name || !price || price <= 0 || price >= 100000) return;
          const imgEl = card.querySelector('img') || (card.tagName === 'IMG' ? card : null);
          const linkEl = card.closest('a[href]') || card.querySelector('a[href]');
          items.push({
            name,
            sp: price,
            mrp: price,
            unit: firstSize(text) || '1 unit',
            img_url: imageSrc(imgEl),
            url: linkEl ? linkEl.href : ''
          });
        });
        const seen = {};
        items = items.filter(item => {
          const key = (item.name + '|' + item.unit + '|' + item.sp).toLowerCase();
          if (seen[key]) return false;
          seen[key] = true;
          return true;
        }).slice(0, 40);
        if (items.length > 0) {
          window.__truecostSwiggySent = true;
          window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: { products: items } }));
          return true;
        }
      } catch(e) {
        window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Resilient fallback failed: ' + e.message }));
      }
      return false;
    }
    if (!extract()) {
      setTimeout(extract, 2000);
      setTimeout(extract, 5000);
      setTimeout(() => { window.scrollTo(0, Math.max(600, document.body.scrollHeight / 2)); extract(); }, 9000);
      setTimeout(() => { window.scrollTo(0, document.body.scrollHeight); extract(); }, 14000);
      setTimeout(() => { window.scrollTo(0, 0); extract(); }, 22000);
    }
  })();
  true;
`;

export default function SwiggyInstamartScraper({ query, latitude = 12.9716, longitude = 77.5946, onResults, onError }: ScraperProps) {
  const webViewRef = useRef<WebView>(null);
  const sentRef = useRef(false);

  useEffect(() => {
    if (!query) return;
    sentRef.current = false;
    console.log(`[SwiggyInstamartScraper] mounted query="${query}" location=${latitude},${longitude}`);
    const timer = setTimeout(() => {
      if (!sentRef.current) {
        const message = `SWIGGY_TIMEOUT Swiggy Instamart did not emit product data for "${query}" within scraper timeout`;
        console.log('[SwiggyInstamartScraper]', message);
        sentRef.current = true;
        onError(message);
      }
    }, 45000);
    return () => clearTimeout(timer);
  }, [latitude, longitude, onError, query]);
  
  const INJECT_BEFORE_LOAD = `
    (function() {
      // 1. Override geolocation for correct city pincode/prices
      const coords = {
        latitude: ${latitude}, longitude: ${longitude},
        accuracy: 10, altitude: null, altitudeAccuracy: null, heading: null, speed: null
      };
      Object.defineProperty(navigator, 'geolocation', {
        value: {
          getCurrentPosition: (s) => s({ coords, timestamp: Date.now() }),
          watchPosition: (s) => { s({ coords, timestamp: Date.now() }); return 0; },
          clearWatch: () => {},
        },
        configurable: true,
      });
      // 2. Intercept search API
      function candidateUrl(url) {
        return typeof url === 'string' && /\\/api\\/instamart\\/search|instamart\\/search|instamart\\/item|widgets|collection|product/i.test(url);
      }
      function looksLikeProductPayload(data) {
        try {
          let count = 0;
          function priceFrom(node) {
            if (!node || typeof node !== 'object') return false;
            const price = node.price || node.pricing || node.offerPrice || node.offer_price || node.finalPrice || node.sellingPrice || node.sp || node.mrp;
            if (typeof price === 'number') return true;
            if (price && typeof price === 'object') {
              return Boolean(price.units || price.value || price.amount || price.offerPrice || price.offer_price || price.finalPrice || price.sellingPrice || price.price || price.sp || price.mrp);
            }
            return false;
          }
          function walk(node) {
            if (!node || count >= 1) return;
            if (Array.isArray(node)) {
              node.forEach(walk);
              return;
            }
            if (typeof node !== 'object') return;
            const hasName = Boolean(node.displayName || node.display_name || node.productName || node.product_name || node.name || node.title);
            const hasVariant = Array.isArray(node.variations) || Array.isArray(node.variants) || Array.isArray(node.productVariants);
            if (hasName && (priceFrom(node) || hasVariant)) {
              count += 1;
              return;
            }
            Object.keys(node).forEach(key => walk(node[key]));
          }
          walk(data);
          return count > 0;
        } catch (e) {
          return false;
        }
      }

      const originalFetch = window.fetch;
      window.fetch = async function(...args) {
        const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
        window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Fetch: ' + url }));
        const response = await originalFetch.apply(this, args);
        if (candidateUrl(url)) {
          try {
            const text = await response.clone().text();
            const data = JSON.parse(text);
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Candidate response keys: ' + Object.keys(data).join(', ') }));
            const isSearchResponse = /\\/api\\/instamart\\/search/i.test(url);
            if (looksLikeProductPayload(data) || (isSearchResponse && data && data.data && !data.error)) {
              if (!window.__truecostSwiggySent) {
                window.__truecostSwiggySent = true;
                window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
              }
            } else if (data && (data.error || data.message)) {
              window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Candidate ignored error: ' + JSON.stringify(data).slice(0, 240) }));
            }
          } catch (e) {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Candidate parse failed: ' + e.message }));
          }
        }
        return response;
      };

      const originalXHR = window.XMLHttpRequest.prototype.open;
      window.XMLHttpRequest.prototype.open = function(method, url) {
        this.addEventListener('load', function() {
          if (candidateUrl(url)) {
            try {
              const data = JSON.parse(this.responseText);
              const isSearchResponse = /\\/api\\/instamart\\/search/i.test(String(url || ''));
              if (looksLikeProductPayload(data) || (isSearchResponse && data && data.data && !data.error)) {
                if (!window.__truecostSwiggySent) {
                  window.__truecostSwiggySent = true;
                  window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
                }
              }
            } catch (e) {
              window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'XHR parse failed: ' + e.message }));
            }
          }
        });
        originalXHR.apply(this, arguments);
      };

      setTimeout(() => {
          fetch('/api/instamart/search/v2?offset=0&query=' + encodeURIComponent(${JSON.stringify(query)}), {
              headers: { 'Accept': 'application/json' }
          }).then(res => res.text()).then(text => {
              const data = JSON.parse(text);
              if (!window.__truecostSwiggySent && looksLikeProductPayload(data)) {
                window.__truecostSwiggySent = true;
                window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
              } else {
                window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Forced search returned non-product payload: ' + text.slice(0, 160) }));
              }
          }).catch(e => {
              window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Forced search fetch failed: ' + e.message }));
          });
      }, 5000);

    })();
    setTimeout(() => window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Page Title: ' + document.title })), 3000);
    true;
  `;

  
  
  const handleLoadEnd = () => {
    if (query) webViewRef.current?.injectJavaScript(RESILIENT_FALLBACK_INJECT);
  };

const onMessage = (event: any) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'LOG') console.log('[SwiggyInstamartScraper] LOG:', data.payload);
      else if (data.type === 'SEARCH_SUCCESS') {
        if (sentRef.current) return;
        sentRef.current = true;
        console.log('[SwiggyInstamartScraper] SEARCH SUCCESS data received!');
        onResults(data.payload);
      }
      else if (data.type === 'SEARCH_ERROR') {
        if (sentRef.current) return;
        sentRef.current = true;
        onError(data.message);
      }
    } catch (_) {}
  };

  return (
    <View style={styles.c}>
      <WebView
        ref={webViewRef}
        source={{uri: query ? `https://www.swiggy.com/instamart/search?custom_back=true&query=${encodeURIComponent(query)}` : 'https://www.swiggy.com/instamart'}}
        injectedJavaScriptBeforeContentLoaded={INJECT_BEFORE_LOAD}
        onMessage={onMessage}
        onLoadStart={() => console.log(`[SwiggyInstamartScraper] load start query="${query}"`)}
        onLoadEnd={() => {
          console.log(`[SwiggyInstamartScraper] load end query="${query}"`);
          handleLoadEnd();
        }}
        onError={event => {
          if (sentRef.current) return;
          const message = event.nativeEvent.description || 'Swiggy Instamart WebView failed to load';
          sentRef.current = true;
          console.log('[SwiggyInstamartScraper] WebView error:', message);
          onError(message);
        }}
        onHttpError={event => {
          if (sentRef.current) return;
          const message = `Swiggy Instamart HTTP ${event.nativeEvent.statusCode}`;
          sentRef.current = true;
          console.log('[SwiggyInstamartScraper] HTTP error:', message);
          onError(message);
        }}
        geolocationEnabled
        
         userAgent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36" javaScriptEnabled domStorageEnabled style={styles.h}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  c: { width: 390, height: 844, position: 'absolute', top: 0, left: 0, opacity: 0.01, overflow: 'hidden' },
  h: { width: 390, height: 844, opacity: 0.01 },
});
