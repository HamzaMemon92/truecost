import React, { useRef } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

interface ScraperProps {
  query: string;
  onResults: (data: any) => void;
  onError: (error: string) => void;
}

// Notion pricing is a static page — we DOM-scrape the price cards
const INJECT_SCRIPT = `
  (function() {
    function extractPricing() {
      const cards = document.querySelectorAll('[class*="pricing"], [class*="plan"], [data-plan]');
      const plans = [];
      document.querySelectorAll('h2, h3').forEach(h => {
        const text = h.textContent || '';
        if (/free|plus|business|enterprise/i.test(text)) {
          const section = h.closest('section, div, article') || h.parentElement;
          const priceEl = section && section.querySelector('[class*="price"], [class*="amount"]');
          const price = priceEl ? priceEl.textContent.replace(/[^\d.]/g, '') : '0';
          plans.push({ name: text.trim(), price: parseFloat(price) || 0 });
        }
      });
      if (plans.length > 0) {
        window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'SEARCH_SUCCESS', payload: { plans } }));
      }
    }
    // Wait for page to fully render
    setTimeout(extractPricing, 2500);
  })();
  true;
`;

export default function NotionScraper({ query, onResults, onError }: ScraperProps) {
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
      <WebView ref={webViewRef} source={{uri: 'https://www.notion.so/pricing'}}
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
