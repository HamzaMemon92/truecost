import React, { useRef } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

interface ScraperProps {
  query: string;
  onResults: (data: any) => void;
  onError: (error: string) => void;
}

// Namma Yatri open-source auto-rickshaw app — intercept fare API
const INJECT_BEFORE_LOAD = `
  (function() {
    const origFetch = window.fetch;
    window.fetch = function(url, ...args) {
      const result = origFetch.apply(this, [url, ...args]);
      result.then(resp => {
        const urlStr = typeof url === 'string' ? url : url.url;
        if (/estimate|fare|ride|quote/i.test(urlStr)) {
          resp.clone().json().then(data => {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: { items: parseNammaFare(data) } }));
          }).catch(() => {});
        }
      });
      return result;
    };

    function parseNammaFare(data) {
      try {
        const quotes = data.quotes || data.fareBreakup || data.estimatedFare || [];
        if (Array.isArray(quotes) && quotes.length > 0) {
          return quotes.map(q => ({
            name: q.vehicleType || q.rideType || 'Auto',
            price: q.estimatedFare || q.maxFare || q.fare || 0,
            delivery_time: (q.eta || q.waitTime || '5') + ' min',
            link: 'https://nammayatri.in/',
          }));
        }
        // Flat fare fallback
        const fare = data.fare || data.estimatedFare || data.maxFare;
        if (fare) {
          return [{ name: 'Auto', price: fare, delivery_time: '5 min', link: 'https://nammayatri.in/' }];
        }
      } catch(e) {}
      return [];
    }
  })();
  true;
`;

export default function NammaYatriScraper({ query, onResults, onError }: ScraperProps) {
  const webViewRef = useRef<WebView>(null);
  
  
  const onMessage = (event: any) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'SEARCH_SUCCESS') onResults(data.payload);
      else if (data.type === 'SEARCH_ERROR') onError(data.message);
    } catch (_) {}
  };

  return (
    <View style={styles.c}>
      <WebView ref={webViewRef} source={{uri: 'https://nammayatri.in/'}}
        onMessage={onMessage}
        
        injectedJavaScriptBeforeContentLoaded={INJECT_BEFORE_LOAD}
         userAgent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36" javaScriptEnabled domStorageEnabled style={styles.h}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  c: { width: 1, height: 1, position: 'absolute', top: -9999, left: -9999, opacity: 0.05 },
  h: { width: 1, height: 1, opacity: 0.05 },
});
