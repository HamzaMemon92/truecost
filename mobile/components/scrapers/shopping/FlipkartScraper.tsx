import React, { useRef, useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

interface ScraperProps {
  query: string;
  onResults: (data: any) => void;
  onError: (error: string) => void;
}

const INJECT_BEFORE_LOAD = `
  (function() {
    function hasProductData(obj) {
      if (!obj || typeof obj !== 'object') return false;
      if (obj.multiWidgetState || obj.RESPONSE || obj.widgetsData || obj.pageDataResponse || obj.slots || obj.products) return true;
      if (Array.isArray(obj) && obj.length > 0) return true;
      return false;
    }

    // 1. Fetch intercept
    const orig = window.fetch;
    window.fetch = async function(...args) {
      const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
      const res = await orig.apply(this, args);
      if (url.includes('/api/4/page/fetch') || url.includes('page/search') ||
          url.includes('/pwa-search-service') || url.includes('/gateway/browsePageDesktop') ||
          (url.includes('flipkart') && url.includes('search'))) {
        try {
          const data = await res.clone().json();
          if (hasProductData(data)) {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
          }
        } catch (e) {}
      }
      return res;
    };

    // 2. XHR intercept
    const OrigXHR = window.XMLHttpRequest;
    window.XMLHttpRequest = function() {
      const xhr = new OrigXHR();
      const origOpen = xhr.open.bind(xhr);
      xhr.open = function(method, url, ...rest) {
        if (typeof url === 'string' && (url.includes('/api/4/page/fetch') || url.includes('search') || url.includes('browsePage'))) {
          xhr.addEventListener('load', function() {
            try {
              const data = JSON.parse(xhr.responseText);
              if (hasProductData(data)) {
                window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: data }));
              }
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

const FALLBACK_INJECT = `
  (function() {
    function extract() {
      try {
        let state = window.__INITIAL_STATE__ || window._state || window.__PRELOADED_STATE__;
        if (state && (state.multiWidgetState || state.pageDataResponse || state.widgetsData)) {
          window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: state }));
          return true;
        }
        let scripts = document.querySelectorAll('script');
        for (let s of scripts) {
          if (s.innerText && s.innerText.includes('window.__INITIAL_STATE__')) {
            let match = s.innerText.match(/window\\.__INITIAL_STATE__\\s*=\\s*({.*});/);
            if (match && match[1]) {
              let parsed = JSON.parse(match[1]);
              if (parsed && (parsed.multiWidgetState || parsed.pageDataResponse)) {
                window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: parsed }));
                return true;
              }
            }
          }
        }
      } catch (e) {}
      return false;
    }

    if (!extract()) {
      setTimeout(extract, 1000);
      setTimeout(extract, 2500);
    }
  })();
  true;
`;

export default function FlipkartScraper({ query, onResults, onError }: ScraperProps) {
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
        source={{ uri: query ? `https://www.flipkart.com/search?q=${encodeURIComponent(query)}` : 'https://www.flipkart.com/' }}
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
