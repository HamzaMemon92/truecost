import React, { useRef } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

interface ScraperProps {
  query: string;
  onResults: (data: any) => void;
  onError: (error: string) => void;
}

const FALLBACK_INJECT = `
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
`;

export default function PharmEasyScraper({ query, onResults, onError }: ScraperProps) {
  const webViewRef = useRef<WebView>(null);
  
  const INJECT_BEFORE_LOAD = `
    (function() {
      // 1. Fetch intercept with broadened URL patterns
      const orig = window.fetch;
      window.fetch = async function(...args) {
        const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
        const res = await orig.apply(this, args);
        if (url.includes('/api/v1/product-service/search') || url.includes('product_search') ||
            url.includes('/search/medicine') || url.includes('search') ||
            url.includes('productList') || url.includes('catalog') || url.includes('medicine')) {
          try {
            const data = await res.clone().json();
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
          } catch (e) {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_ERROR', message: String(e) }));
          }
        }
        return res;
      };

      // 2. XHR intercept — PharmEasy uses XHR heavily
      const OrigXHR = window.XMLHttpRequest;
      window.XMLHttpRequest = function() {
        const xhr = new OrigXHR();
        const origOpen = xhr.open.bind(xhr);
        xhr.open = function(method, url, ...rest) {
          if (typeof url === 'string' && (url.includes('search') || url.includes('product') || url.includes('medicine'))) {
            xhr.addEventListener('load', function() {
              try {
                const data = JSON.parse(xhr.responseText);
                window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
              } catch (e) {}
            });
          }
          return origOpen(method, url, ...rest);
        };
        return xhr;
      };
    })();
    true;
  `;

  
  
  const handleLoadEnd = () => {
    if (query) webViewRef.current?.injectJavaScript(FALLBACK_INJECT);
  };

const onMessage = (event: any) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'SEARCH_SUCCESS') onResults(data.payload);
      else if (data.type === 'SEARCH_ERROR') onError(data.message);
    } catch (_) {}
  };

  return (
    <View style={styles.c}>
      <WebView
        ref={webViewRef}
        source={{uri: query ? `https://pharmeasy.in/search/all?name=${encodeURIComponent(query)}` : 'https://pharmeasy.in/'}}
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
