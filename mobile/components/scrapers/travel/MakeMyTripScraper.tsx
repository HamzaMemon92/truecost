import React, { useRef } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

interface ScraperProps {
  query: string;
  onResults: (data: any) => void;
  onError: (error: string) => void;
}

export default function MakeMyTripScraper({ query, onResults, onError }: ScraperProps) {
  const webViewRef = useRef<WebView>(null);
  
  const INJECT_BEFORE_LOAD = `
    (function() {
      // Fetch intercept — MMT flight search API patterns
      const origFetch = window.fetch;
      window.fetch = async function(...args) {
        const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
        const res = await origFetch.apply(this, args);
        if (url.includes('air-search-svc') || url.includes('fssc') || url.includes('flights/results') ||
            url.includes('/getFlightData') || url.includes('sfc.makemytrip') ||
            url.includes('searchResponse') || url.includes('getfarecard') ||
            url.includes('/flifo') || url.includes('itinerary')) {
          try {
            const data = await res.clone().json();
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
          } catch (e) {}
        }
        return res;
      };

      // XHR intercept (MMT uses both)
      const XHROrig = window.XMLHttpRequest;
      window.XMLHttpRequest = function() {
        const xhr = new XHROrig();
        const origOpen = xhr.open.bind(xhr);
        xhr.open = function(method, url, ...rest) {
          if (typeof url === 'string' && (url.includes('air-search') || url.includes('fssc') ||
              url.includes('sfc.makemytrip') || url.includes('searchResponse') || url.includes('flight'))) {
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
        source={{uri: query ? `https://www.makemytrip.com/flights/search?q=${encodeURIComponent(query)}` : 'https://www.makemytrip.com/flights/'}}
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
