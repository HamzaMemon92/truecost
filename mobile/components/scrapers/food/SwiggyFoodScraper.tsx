import React, { useRef } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

interface ScraperProps {
  query: string;
  latitude?: number;
  longitude?: number;
  onResults: (data: any) => void;
  onError: (error: string) => void;
}

export default function SwiggyFoodScraper({ query, latitude = 12.9716, longitude = 77.5946, onResults, onError }: ScraperProps) {
  const webViewRef = useRef<WebView>(null);
  
  // Injected BEFORE page JS runs — overrides navigator.geolocation so Swiggy
  // sees the user's real city and returns correct restaurant listings
  const INJECT_BEFORE_LOAD = `
    (function() {
      // 1. Override geolocation so Swiggy loads correct city restaurants
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

      // 2. Intercept search API responses
      const orig = window.fetch;
      window.fetch = async function(...args) {
        const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
        const res = await orig.apply(this, args);
        if (url.includes('/dapi/restaurants/list') || url.includes('restaurants/search') ||
            url.includes('food-service') || url.includes('/api/restaurants') ||
            url.includes('/v4/restaurants') || url.includes('/search?') && url.includes('swiggy')) {
          try {
            const data = await res.clone().json();
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
          } catch (e) {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_ERROR', message: String(e) }));
          }
        }
        return res;
      };
      // XHR backup
      const OrigXHR = window.XMLHttpRequest;
      window.XMLHttpRequest = function() {
        const xhr = new OrigXHR();
        const origOpen = xhr.open.bind(xhr);
        xhr.open = function(method, url, ...rest) {
          if (typeof url === 'string' && (url.includes('restaurant') || url.includes('search'))) {
            xhr.addEventListener('load', function() {
              try {
                const data = JSON.parse(xhr.responseText);
                window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
              } catch(e) {}
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

  return (
    <View style={styles.c}>
      <WebView
        ref={webViewRef}
        source={{uri: query ? `https://www.swiggy.com/search?query=${encodeURIComponent(query)}` : 'https://www.swiggy.com/'}}
        injectedJavaScriptBeforeContentLoaded={INJECT_BEFORE_LOAD}
        onMessage={onMessage}
        
         userAgent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36" javaScriptEnabled
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
