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
    function extract() {
      try {
        if (window.__PRELOADED_STATE__) {
            window.__truecostBigBasketSent = true;
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
            window.__truecostBigBasketSent = true;
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: { products: items } }));
          }
        }
      } catch(e) {}
    }
    setTimeout(extract, 2000);
  })();
  true;
`;

export default function BigBasketScraper({ query, latitude = 12.9716, longitude = 77.5946, onResults, onError }: ScraperProps) {
  const webViewRef = useRef<WebView>(null);
  const sentRef = useRef(false);
  
  const INJECT_BEFORE_LOAD = `
    (function() {
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
      const orig = window.fetch;
      window.fetch = async function(...args) {
        const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
        const res = await orig.apply(this, args);
        if (url.includes('/listing-svc/v2/products')) {
          try {
            const data = await res.clone().json();
            if (!window.__truecostBigBasketSent) {
              window.__truecostBigBasketSent = true;
              window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
            }
          } catch (e) {}
        }
        return res;
      };

      const originalXHR = window.XMLHttpRequest.prototype.open;
      window.XMLHttpRequest.prototype.open = function(method, url) {
        this.addEventListener('load', function() {
          if (typeof url === 'string' && url.includes('/listing-svc/v2/products')) {
            try {
              const data = JSON.parse(this.responseText);
              if (!window.__truecostBigBasketSent) {
                window.__truecostBigBasketSent = true;
                window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
              }
            } catch (e) {}
          }
        });
        originalXHR.apply(this, arguments);
      };

      setTimeout(() => {
          fetch('/listing-svc/v2/products?type=ps&page=1&slug=' + encodeURIComponent('${query}'), {
              headers: { 'Accept': 'application/json' }
          }).then(res => res.json()).then(data => {
              if (!window.__truecostBigBasketSent) {
                window.__truecostBigBasketSent = true;
                window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
              }
          }).catch(e => {});
      }, 5000);

    })();
    setTimeout(() => window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Page Title: ' + document.title })), 3000);
    true;
  `;

  
  
  const handleLoadEnd = () => {
    if (query) webViewRef.current?.injectJavaScript(FALLBACK_INJECT);
  };

  useEffect(() => {
    if (!query) return;
    sentRef.current = false;
    const timer = setTimeout(() => {
      if (!sentRef.current) {
        const message = `BIGBASKET_TIMEOUT BigBasket did not emit product data for "${query}" within scraper timeout`;
        console.log('[BigBasketScraper]', message);
        sentRef.current = true;
        onError(message);
      }
    }, 32000);
    return () => clearTimeout(timer);
  }, [onError, query]);

const onMessage = (event: any) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'LOG') console.log('[BigBasketScraper] LOG:', data.payload);
      else if (data.type === 'SEARCH_SUCCESS') {
        if (sentRef.current) return;
        sentRef.current = true;
        onResults(data.payload);
      }
      else if (data.type === 'SEARCH_ERROR') {
        if (sentRef.current) return;
        sentRef.current = true;
        onError(data.message || 'BIGBASKET_PROVIDER_ERROR');
      }
    } catch (_) {}
  };

  return (
    <View style={styles.c}>
      <WebView
        ref={webViewRef}
        source={{uri: query ? `https://www.bigbasket.com/ps/?q=${encodeURIComponent(query)}&nc=as` : 'https://www.bigbasket.com/'}}
        injectedJavaScriptBeforeContentLoaded={INJECT_BEFORE_LOAD}
        onMessage={onMessage}
        onLoadEnd={handleLoadEnd}
        onError={event => {
          if (sentRef.current) return;
          const message = event.nativeEvent.description || 'BIGBASKET_NETWORK_FAILURE BigBasket WebView failed to load';
          sentRef.current = true;
          console.log('[BigBasketScraper] WebView error:', message);
          onError(message);
        }}
        onHttpError={event => {
          if (sentRef.current) return;
          const message = `BIGBASKET_HTTP_ERROR status=${event.nativeEvent.statusCode}`;
          sentRef.current = true;
          console.log('[BigBasketScraper] HTTP error:', message);
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
