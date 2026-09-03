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

// PaisaBazaar: https://www.paisabazaar.com/ — credit cards, loans, FDs
// API: /api/v1/products or /credit-card/search or /loan/search
const INJECT_BEFORE_LOAD = `
  (function() {
    const origFetch = window.fetch;
    window.fetch = async function(...args) {
      const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
      const res = await origFetch.apply(this, args);
      if (url.includes('/api/') && (url.includes('search') || url.includes('loan') || url.includes('credit') || url.includes('product') || url.includes('card'))) {
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
        if (url.includes('/api/') && (url.includes('search') || url.includes('loan') || url.includes('credit'))) {
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

export default function PaisaBazaarScraper({ query, onResults, onError }: ScraperProps) {
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
      <WebView
        ref={webViewRef}
        source={{uri: query ? `https://www.paisabazaar.com/search/?q=${encodeURIComponent(query)}` : 'https://www.paisabazaar.com/'}}
        injectedJavaScriptBeforeContentLoaded={INJECT_BEFORE_LOAD}
        onMessage={onMessage}
        
         userAgent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36" javaScriptEnabled domStorageEnabled style={styles.h}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  c: { width: 1, height: 1, position: 'absolute', top: -9999, left: -9999, opacity: 0.05 },
  h: { width: 1, height: 1, opacity: 0.05 },
});
