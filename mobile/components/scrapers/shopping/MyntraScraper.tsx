import React, { useRef, useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

interface ScraperProps {
  query: string;
  onResults: (data: any) => void;
  onError: (error: string) => void;
  latitude?: number;
  longitude?: number;
}

const INJECT_BEFORE_LOAD = `
  (function() {
    function hasData(obj) {
      if (!obj || typeof obj !== 'object') return false;
      if (obj.results || obj.products || obj.productList || obj.items || obj.data) return true;
      if (Array.isArray(obj) && obj.length > 0) return true;
      return false;
    }

    const origFetch = window.fetch;
    window.fetch = async function(...args) {
      const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
      const res = await origFetch.apply(this, args);
      if (url.includes('/gateway/v2/search') || url.includes('/searchandfilter') || url.includes('/search/') || url.includes('quicksearch')) {
        try {
          const data = await res.clone().json();
          if (hasData(data)) {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
          }
        } catch(e) {}
      }
      return res;
    };

    const origOpen = XMLHttpRequest.prototype.open;
    const origSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
      this._url = url;
      return origOpen.call(this, method, url, ...rest);
    };
    XMLHttpRequest.prototype.send = function(...args) {
      this.addEventListener('load', function() {
        const url = this._url || '';
        if (url.includes('/gateway/v2/search') || url.includes('/searchandfilter')) {
          try {
            const data = JSON.parse(this.responseText);
            if (hasData(data)) {
              window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
            }
          } catch(e) {}
        }
      });
      return origSend.apply(this, args);
    };
  })();
  true;
`;

const FALLBACK_INJECT = `
  (function() {
    function extract() {
      try {
        const items = document.querySelectorAll('.product-base, li.product-base, [class*="product-base"]');
        if (items && items.length > 0) {
          let products = [];
          items.forEach(function(p) {
            try {
              const brandEl = p.querySelector('.product-brand, h3, [class*="Brand"]');
              const nameEl = p.querySelector('.product-product, h4, [class*="Product"]');
              const priceEl = p.querySelector('.product-discountedPrice, .product-price span, [class*="Price"]');
              const imgEl = p.querySelector('img.img-responsive, img');
              const linkEl = p.querySelector('a');

              if (nameEl && priceEl) {
                const brand = brandEl ? brandEl.textContent.trim() : 'Myntra';
                const name = nameEl.textContent.trim();
                const price = parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10);
                if (price > 0) {
                  let img = imgEl ? (imgEl.getAttribute('src') || '') : '';
                  let href = linkEl ? (linkEl.getAttribute('href') || '') : '';
                  products.push({
                    productName: brand + ' ' + name,
                    brandName: brand,
                    price: { discounted: price, mrp: price },
                    landingPageUrl: href,
                    images: [{ src: img }]
                  });
                }
              }
            } catch(e) {}
          });
          if (products.length > 0) {
            window.ReactNativeWebView.postMessage(JSON.stringify({
              type: 'SEARCH_SUCCESS',
              payload: { products: products.slice(0, 15) }
            }));
            return true;
          }
        }

        if (window.__myx && window.__myx.searchData && window.__myx.searchData.results) {
          try {
            window.ReactNativeWebView.postMessage(JSON.stringify({
              type: 'SEARCH_SUCCESS',
              payload: window.__myx.searchData.results
            }));
            return true;
          } catch (err) {}
        }
      } catch (e) {}
      return false;
    }

    if (!extract()) {
      setTimeout(extract, 1000);
      setTimeout(extract, 2500);
      setTimeout(extract, 4000);
    }
  })();
  true;
`;

function getMyntraUrl(q: string): string {
  if (!q) return 'https://www.myntra.com/';
  const slug = q.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-');
  return `https://www.myntra.com/${slug}`;
}

export default function MyntraScraper({ query, onResults, onError }: ScraperProps) {
  const webViewRef = useRef<WebView>(null);


  const onMessage = (event: any) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'SEARCH_SUCCESS') onResults(data.payload);
      else if (data.type === 'SEARCH_ERROR') onError(data.message);
    } catch (_) {}
  };

  const handleLoadEnd = () => {
    if (query) {
      webViewRef.current?.injectJavaScript(FALLBACK_INJECT);
    }
  };

  return (
    <View style={styles.c}>
      <WebView
        ref={webViewRef}
        source={{ uri: getMyntraUrl(query) }}
        injectedJavaScriptBeforeContentLoaded={INJECT_BEFORE_LOAD}
        onMessage={onMessage}
        onLoadEnd={handleLoadEnd}
        userAgent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
        javaScriptEnabled
        domStorageEnabled
        style={styles.h}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  c: { width: 1, height: 1, position: 'absolute', top: -9999, left: -9999, opacity: 0.05 },
  h: { width: 1, height: 1, opacity: 0.05 },
});
