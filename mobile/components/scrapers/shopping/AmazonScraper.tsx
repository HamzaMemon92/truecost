import React, { useRef, useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

interface ScraperProps {
  query: string;
  onResults: (data: any) => void;
  onError: (error: string) => void;
}

const EXTRACT_AMAZON_DOM = `
  (function() {
    function scrape() {
      try {
        const items = document.querySelectorAll('[data-component-type="s-search-result"], .s-result-item[data-asin]');
        if (!items || items.length === 0) return false;
        let results = [];
        items.forEach(function(p) {
          try {
            const titleEl = p.querySelector('h2 span, h2 a span, .a-size-medium, .a-size-base-plus, [class*="title"]');
            const priceEl = p.querySelector('.a-price .a-price-whole, .a-price-whole, .a-price');
            const imgEl = p.querySelector('.s-image, img');
            const linkEl = p.querySelector('h2 a, a.a-link-normal');
            
            if (titleEl && priceEl) {
              const title = titleEl.textContent.trim();
              const priceText = priceEl.textContent.replace(/[^0-9]/g, '');
              const price = parseInt(priceText, 10);
              if (title && price > 0) {
                let imgUrl = imgEl ? (imgEl.getAttribute('src') || imgEl.getAttribute('data-src') || '') : '';
                let href = linkEl ? linkEl.getAttribute('href') : '';
                if (href && !href.startsWith('http')) href = 'https://www.amazon.in' + href;
                results.push({
                  name: title,
                  price: price,
                  image: imgUrl,
                  url: href || 'https://www.amazon.in'
                });
              }
            }
          } catch(e) {}
        });

        if (results.length > 0) {
          window.ReactNativeWebView.postMessage(JSON.stringify({
            type: 'SEARCH_SUCCESS',
            payload: { amazonData: results.slice(0, 15) }
          }));
          return true;
        }
      } catch(e) {}
      return false;
    }

    // Try immediately, and then retry after 1s, 2.5s, 4s
    if (!scrape()) {
      setTimeout(scrape, 1000);
      setTimeout(scrape, 2500);
      setTimeout(scrape, 4000);
    }
  })();
  true;
`;

export default function AmazonScraper({ query, onResults, onError }: ScraperProps) {
  const webViewRef = useRef<WebView>(null);

  const INJECT_BEFORE_LOAD = `
    (function() {
      function hasProducts(d) {
        if (!d || typeof d !== 'object') return false;
        if (d.amazonData && Array.isArray(d.amazonData) && d.amazonData.length > 0) return true;
        if (d.items && Array.isArray(d.items) && d.items.length > 0) return true;
        if (d.results && Array.isArray(d.results) && d.results.length > 0) return true;
        if (d.products && Array.isArray(d.products) && d.products.length > 0) return true;
        return false;
      }

      // Fetch intercept
      const origFetch = window.fetch;
      window.fetch = async function(...args) {
        const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
        const res = await origFetch.apply(this, args);
        if (url.includes('/s/query') || url.includes('P13NSearchResults') || url.includes('/api/search')) {
          try {
            const data = await res.clone().json();
            if (hasProducts(data)) {
              window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
            }
          } catch (e) {}
        }
        return res;
      };

      // XHR intercept
      const OrigXHR = window.XMLHttpRequest;
      window.XMLHttpRequest = function() {
        const xhr = new OrigXHR();
        const origOpen = xhr.open.bind(xhr);
        xhr.open = function(method, url, ...rest) {
          if (typeof url === 'string' && (url.includes('P13NSearchResults') || url.includes('/s/query'))) {
            xhr.addEventListener('load', function() {
              try {
                const data = JSON.parse(xhr.responseText);
                if (hasProducts(data)) {
                  window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
                }
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


  const onMessage = (event: any) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'SEARCH_SUCCESS') onResults(data.payload);
      else if (data.type === 'SEARCH_ERROR') onError(data.message);
    } catch (_) {}
  };

  const handleLoadEnd = () => {
    if (query) {
      webViewRef.current?.injectJavaScript(EXTRACT_AMAZON_DOM);
    }
  };

  return (
    <View style={styles.c}>
      <WebView
        ref={webViewRef}
        source={{ uri: query ? `https://www.amazon.in/s?k=${encodeURIComponent(query)}` : 'https://www.amazon.in/' }}
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
