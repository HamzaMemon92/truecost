import React, { useRef } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

interface ScraperProps {
  query: string;
  onResults: (data: any) => void;
  onError: (error: string) => void;
  latitude?: number;
  longitude?: number;
}

// Netmeds: https://www.netmeds.com/catalogsearch/result?q=<query>
// API: /api/v1.9/pub/catalog/product or /catalogsearch/result
const INJECT_BEFORE_LOAD = `
  (function() {
    const origFetch = window.fetch;
    window.fetch = async function(...args) {
      const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
      const res = await origFetch.apply(this, args);
      if (url.includes('/catalog') || url.includes('/search') || url.includes('product') || url.includes('medicine')) {
        try {
          const data = await res.clone().json();
          window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
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
        if (url.includes('/catalog') || url.includes('/search')) {
          try {
            const data = JSON.parse(this.responseText);
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
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
`;

export default function NetmedsScraper({ query, onResults, onError }: ScraperProps) {
  const webViewRef = useRef<WebView>(null);
  
  
  
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
        source={{uri: query ? `https://www.netmeds.com/catalogsearch/result?q=${encodeURIComponent(query)}` : 'https://www.netmeds.com/'}}
        injectedJavaScriptBeforeContentLoaded={INJECT_BEFORE_LOAD}
        onMessage={onMessage}
        onLoadEnd={handleLoadEnd}
        
         userAgent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36" javaScriptEnabled domStorageEnabled style={styles.h}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  c: { width: 1, height: 1, position: 'absolute', top: -9999, left: -9999, opacity: 0.05 },
  h: { width: 1, height: 1, opacity: 0.05 },
});
