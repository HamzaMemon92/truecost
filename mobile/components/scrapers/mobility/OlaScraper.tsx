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

export default function OlaScraper({ query, latitude = 12.9716, longitude = 77.5946, onResults, onError }: ScraperProps) {
  const webViewRef = useRef<WebView>(null);
  
  const INJECT_BEFORE_LOAD = `
    (function() {
      // 1. Geolocation override for city-accurate prices
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

      // 2. Fetch intercept
      const orig = window.fetch;
      window.fetch = async function(...args) {
        const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
        const res = await orig.apply(this, args);
        if (url.includes('/v1/products') || url.includes('/v1/fare') || url.includes('/v1/services') ||
            url.includes('getEstimate') || url.includes('/v2/categories') || url.includes('/v1/categories') ||
            url.includes('serviceTypes') || url.includes('ride_estimate')) {
          try {
            const data = await res.clone().json();
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
          } catch (e) {}
        }
        return res;
      };

      // 3. XHR intercept
      const OrigXHR = window.XMLHttpRequest;
      window.XMLHttpRequest = function() {
        const xhr = new OrigXHR();
        const origOpen = xhr.open.bind(xhr);
        xhr.open = function(method, url, ...rest) {
          if (typeof url === 'string' && (url.includes('fare') || url.includes('estimate') ||
              url.includes('products') || url.includes('serviceTypes'))) {
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
        source={{uri: `https://book.olacabs.com/?pickup_lat=${latitude}&pickup_lng=${longitude}&serviceType=p2p`}}
        injectedJavaScriptBeforeContentLoaded={INJECT_BEFORE_LOAD}
        onMessage={onMessage}
        
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
