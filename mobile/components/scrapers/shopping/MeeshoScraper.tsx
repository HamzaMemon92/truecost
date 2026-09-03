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
      if (obj.products || obj.productList || obj.items || obj.data || obj.catalogue || obj.catalogs) return true;
      if (Array.isArray(obj) && obj.length > 0) return true;
      return false;
    }

    const origFetch = window.fetch;
    window.fetch = async function(...args) {
      const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
      const res = await origFetch.apply(this, args);
      if (url.includes('/products/search') || url.includes('search_products') || url.includes('/catalog') || url.includes('graphql')) {
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
        if (url.includes('/products/search') || url.includes('search_products') || url.includes('/catalog')) {
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
        const cards = document.querySelectorAll('[class*="ProductCard"], [class*="product-card"], a[href*="/p/"]');
        if (cards && cards.length > 0) {
          let items = [];
          cards.forEach(function(c) {
            try {
              const titleEl = c.querySelector('p, span[class*="title"], h5, [class*="Title"]');
              const priceEl = c.querySelector('h5, [class*="Price"], [class*="price"], h4');
              const imgEl = c.querySelector('img');
              const href = c.getAttribute('href') || (c.querySelector('a') ? c.querySelector('a').getAttribute('href') : '');

              if (titleEl && priceEl) {
                const title = titleEl.textContent.trim();
                const price = parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10);
                if (title && price > 0) {
                  let img = imgEl ? (imgEl.getAttribute('src') || '') : '';
                  items.push({
                    productName: title,
                    discountedPrice: price,
                    images: [img],
                    slug: href ? href.replace(/^\\/p\\//, '') : ''
                  });
                }
              }
            } catch(e) {}
          });
          if (items.length > 0) {
            window.ReactNativeWebView.postMessage(JSON.stringify({
              type: 'SEARCH_SUCCESS',
              payload: { products: items.slice(0, 15) }
            }));
            return true;
          }
        }

        let state = window.__PRELOADED_STATE__ || window.__INITIAL_STATE__ || window._state;
        if (state) {
          try {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: state }));
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

export default function MeeshoScraper({ query, onResults, onError }: ScraperProps) {
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
        source={{ uri: query ? `https://www.meesho.com/search?q=${encodeURIComponent(query)}` : 'https://www.meesho.com/' }}
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
