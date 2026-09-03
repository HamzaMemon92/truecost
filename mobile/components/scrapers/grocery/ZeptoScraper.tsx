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
            window.__truecostZeptoSent = true;
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
`;

export default function ZeptoScraper({ query, latitude = 12.9716, longitude = 77.5946, onResults, onError }: ScraperProps) {
  const webViewRef = useRef<WebView>(null);
  const sentRef = useRef(false);
  
  // Injected BEFORE page JS runs — overrides navigator.geolocation so Zepto
  // sees the user's real city and returns correct pin-code prices
  const INJECT_BEFORE_LOAD = `
    (function() {
      // 1. Override geolocation so Zepto loads correct city prices
      const coords = {
        latitude: ${latitude},
        longitude: ${longitude},
        accuracy: 10, altitude: null, altitudeAccuracy: null, heading: null, speed: null
      };
      Object.defineProperty(navigator, 'geolocation', {
        value: {
          getCurrentPosition: (success) => success({ coords, timestamp: Date.now() }),
          watchPosition: (success) => { success({ coords, timestamp: Date.now() }); return 0; },
          clearWatch: () => {},
        },
        configurable: true,
      });

      // 2. Intercept fetch — catch Zepto's /api/v3/search response
      const orig = window.fetch;
      window.fetch = async function(...args) {
        const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
        const res = await orig.apply(this, args);
        // Zepto uses /api/v3/search or /v3/search-service
        if (url.includes('/v3/search') || url.includes('search-service') || url.includes('/api/v2/search')) {
          try {
            const data = await res.clone().json();
            if (!window.__truecostZeptoSent) {
              window.__truecostZeptoSent = true;
              window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
            }
          } catch (e) {}
        }
        return res;
      };

      // 3. Intercept XHR as backup
      const XHR = XMLHttpRequest.prototype;
      const open = XHR.open;
      const send = XHR.send;
      XHR.open = function(method, url) {
          this._url = url;
          return open.apply(this, arguments);
      };
      XHR.send = function() {
          this.addEventListener('load', function() {
              if (this._url && (this._url.includes('/v3/search') || this._url.includes('search-service'))) {
                  try {
                      const data = JSON.parse(this.responseText);
                      if (!window.__truecostZeptoSent) {
                        window.__truecostZeptoSent = true;
                        window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
                      }
                  } catch(e) {}
              }
          });
          return send.apply(this, arguments);
      };

      window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Injection complete' }));
    })();
    setTimeout(() => {
      window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'LOG', payload: 'Page Title: ' + document.title }));
    }, 4000);
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
        const message = `ZEPTO_TIMEOUT Zepto did not emit product data for "${query}" within scraper timeout`;
        console.log('[ZeptoScraper]', message);
        sentRef.current = true;
        onError(message);
      }
    }, 32000);
    return () => clearTimeout(timer);
  }, [onError, query]);

const onMessage = (event: any) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'LOG') console.log('[ZeptoScraper LOG]', data.payload);
      else if (data.type === 'SEARCH_SUCCESS') {
        if (sentRef.current) return;
        sentRef.current = true;
        console.log('[ZeptoScraper SUCCESS]');
        onResults(data.payload);
      }
      else if (data.type === 'SEARCH_ERROR') {
        if (sentRef.current) return;
        sentRef.current = true;
        console.error('[ZeptoScraper ERROR]', data.message);
        onError(data.message);
      }
    } catch (_) {}
  };

  return (
    <View style={styles.c}>
      <WebView
        ref={webViewRef}
        source={{uri: query ? `https://www.zeptonow.com/search?query=${encodeURIComponent(query)}` : 'https://www.zeptonow.com/'}}
        injectedJavaScriptBeforeContentLoaded={INJECT_BEFORE_LOAD}
        onMessage={onMessage}
        onLoadEnd={handleLoadEnd}
        onError={event => {
          if (sentRef.current) return;
          const message = event.nativeEvent.description || 'ZEPTO_NETWORK_FAILURE Zepto WebView failed to load';
          sentRef.current = true;
          console.log('[ZeptoScraper ERROR]', message);
          onError(message);
        }}
        onHttpError={event => {
          if (sentRef.current) return;
          const message = `ZEPTO_HTTP_ERROR status=${event.nativeEvent.statusCode}`;
          sentRef.current = true;
          console.log('[ZeptoScraper ERROR]', message);
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
