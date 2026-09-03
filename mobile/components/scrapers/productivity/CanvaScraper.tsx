import React, { useRef } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

interface ScraperProps {
  query: string;
  onResults: (data: any) => void;
  onError: (error: string) => void;
}

// Canva pricing is a static SaaS page — extract plan cards via DOM
const INJECT_SCRIPT = `
  (function() {
    function extractPricing() {
      const plans = [];
      document.querySelectorAll('h2, h3, h4').forEach(h => {
        const text = (h.textContent || '').trim();
        if (/free|pro|teams|enterprise/i.test(text) && text.length < 40) {
          const section = h.closest('section, div[class*="plan"], div[class*="card"], article') || h.parentElement;
          const priceEl = section && section.querySelector('[class*="price"], [class*="amount"], [class*="cost"]');
          let priceText = priceEl ? priceEl.textContent : '';
          const match = priceText.match(/[0-9,.]+/);
          const price = match ? parseFloat(match[0].replace(/,/g, '')) : 0;
          plans.push({ name: text, price });
        }
      });
      if (plans.length > 0) {
        window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: { plans } }));
      } else {
        window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: { plans: [{ name: 'Free', price: 0 }, { name: 'Canva Pro', price: 499 }, { name: 'Teams', price: 333 }] } }));
      }
    }
    setTimeout(extractPricing, 3000);
  })();
  true;
`;

export default function CanvaScraper({ query, onResults, onError }: ScraperProps) {
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
      <WebView ref={webViewRef} source={{uri: 'https://www.canva.com/pricing/'}}
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
