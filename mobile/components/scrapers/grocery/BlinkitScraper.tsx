import React, { useEffect, useMemo, useRef } from 'react';
import { View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

interface ScraperProps {
  query: string;
  latitude?: number;
  longitude?: number;
  onResults: (data: any) => void;
  onError: (error: string) => void;
}

function blinkitScript(query: string, latitude: number, longitude: number) {
  const inputQuery = JSON.stringify(query);
  const encodedQuery = JSON.stringify(encodeURIComponent(query));

  return `
    (function() {
      if (window.__tcBlinkitInstalled) return true;
      window.__tcBlinkitInstalled = true;

      const INPUT_QUERY = ${inputQuery};
      const ENCODED_QUERY = ${encodedQuery};
      const PRODUCT_WORDS = INPUT_QUERY.toLowerCase().split(/\\s+/).filter(Boolean);
      const MAX_SAMPLE_TEXT = 260;
      const diag = window.__tcBlinkitDiag = {
        input_query: INPUT_QUERY,
        encoded_query: ENCODED_QUERY,
        query_sent_to_blinkit: '',
        started_at: Date.now(),
        location: { latitude: ${latitude}, longitude: ${longitude} },
        fetch_count: 0,
        xhr_count: 0,
        candidate_api_responses: 0,
        json_responses: 0,
        html_responses: 0,
        product_like_responses: 0,
        raw_product_objects: 0,
        parsed_products: 0,
        dom_product_nodes: 0,
        body_chars: 0,
        challenge_detected: false,
        location_gate_detected: false,
        login_detected: false,
        response_samples: [],
        product_samples: [],
        final_url: '',
        title: ''
      };

      function post(type, payload) {
        try { window.ReactNativeWebView.postMessage(JSON.stringify({ type, payload })); } catch (_) {}
      }

      function postSuccess(payload) {
        diag.success_emitted = true;
        post('SEARCH_SUCCESS', payload);
      }

      function log(message) {
        post('LOG', message);
      }

      function cleanText(value) {
        return String(value || '').replace(/\\s+/g, ' ').trim();
      }

      function compactUrl(value) {
        return String(value || '').replace(/([?&](?:token|key|session|sid|auth|device_id|user_id|cookie|csrf)[^=&]*=)[^&]+/ig, '$1[redacted]');
      }

      function textContainsProductWords(text) {
        const haystack = cleanText(text).toLowerCase();
        return PRODUCT_WORDS.some(word => word.length > 2 && haystack.includes(word));
      }

      function priceFrom(value) {
        if (value == null) return null;
        if (typeof value === 'number') return value > 999 ? Math.round(value / 100) : value;
        if (typeof value === 'object') {
          const keys = ['price', 'mrp', 'sp', 'selling_price', 'sellingPrice', 'final_price', 'finalPrice', 'offer_price', 'offerPrice', 'amount', 'units', 'value'];
          for (const key of keys) {
            if (Object.prototype.hasOwnProperty.call(value, key)) {
              const nested = priceFrom(value[key]);
              if (nested) return nested;
            }
          }
          return null;
        }
        const match = String(value).match(/(?:₹|Rs\\.?|INR)?\\s*([0-9]+(?:\\.[0-9]+)?)/i);
        if (!match) return null;
        const number = Number(match[1]);
        return Number.isFinite(number) ? number : null;
      }

      function firstText(obj, keys) {
        if (!obj || typeof obj !== 'object') return '';
        for (const key of keys) {
          const value = obj[key];
          if (typeof value === 'string' && cleanText(value)) return cleanText(value);
          if (value && typeof value === 'object' && typeof value.text === 'string') return cleanText(value.text);
        }
        return '';
      }

      function firstImage(obj) {
        if (!obj || typeof obj !== 'object') return '';
        const direct = firstText(obj, ['image', 'image_url', 'imageUrl', 'img_url', 'thumbnail', 'thumbnail_url', 'media_url']);
        if (direct) return direct;
        for (const key of ['images', 'imageUrls', 'media', 'assets']) {
          const value = obj[key];
          if (Array.isArray(value)) {
            for (const item of value) {
              if (typeof item === 'string') return item;
              const nested = firstImage(item);
              if (nested) return nested;
            }
          } else if (value && typeof value === 'object') {
            const nested = firstImage(value);
            if (nested) return nested;
          }
        }
        return '';
      }

      function firstUrl(obj) {
        return firstText(obj, ['url', 'product_url', 'productUrl', 'deeplink', 'deep_link', 'web_url', 'webUrl']);
      }

      function productId(obj) {
        return firstText(obj, ['product_id', 'productId', 'id', 'sku_id', 'skuId', 'variant_id', 'variantId', 'nav_id']) || cleanText(obj && obj.id);
      }

      function unitFrom(obj) {
        return firstText(obj, ['unit', 'weight', 'weightVolume', 'weight_volume', 'pack_size', 'packSize', 'formattedPacksize', 'quantity', 'quantityDescription', 'variant']);
      }

      function nameFrom(obj) {
        return firstText(obj, ['product_name', 'productName', 'display_name', 'displayName', 'name', 'title', 'item_name', 'itemName']);
      }

      function mrpFrom(obj, fallback) {
        return priceFrom(obj && (obj.mrp || obj.original_price || obj.originalPrice || obj.list_price || obj.listPrice || obj.striked_price || obj.strikedPrice)) || fallback;
      }

      function sellingPriceFrom(obj) {
        return priceFrom(obj && (obj.sp || obj.price || obj.selling_price || obj.sellingPrice || obj.final_price || obj.finalPrice || obj.offer_price || obj.offerPrice));
      }

      function availabilityFrom(obj) {
        const raw = obj && (obj.in_stock ?? obj.inStock ?? obj.available ?? obj.isAvailable ?? obj.inventory ?? obj.availability);
        if (typeof raw === 'boolean') return raw;
        if (typeof raw === 'number') return raw > 0;
        if (typeof raw === 'string') return !/out|sold|unavailable/i.test(raw);
        if (raw && typeof raw === 'object') return availabilityFrom(raw);
        return null;
      }

      function maybeProduct(obj) {
        if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return null;
        const name = nameFrom(obj);
        const price = sellingPriceFrom(obj);
        const unit = unitFrom(obj);
        if (!name || !price || price <= 0 || price > 100000) return null;
        const objectText = cleanText(JSON.stringify(obj).slice(0, 2000));
        if (!textContainsProductWords(name + ' ' + objectText)) return null;
        return {
          name,
          brand: firstText(obj, ['brand', 'brandName', 'manufacturer']) || (name.toLowerCase().includes('amul') ? 'Amul' : 'Blinkit'),
          sp: price,
          mrp: mrpFrom(obj, price),
          unit: unit || '1 unit',
          img_url: firstImage(obj),
          nav_id: productId(obj) || name,
          url: firstUrl(obj),
          in_stock: availabilityFrom(obj),
          source: 'blinkit_network'
        };
      }

      function collectProducts(root) {
        const products = [];
        const seenNodes = new Set();
        function walk(node) {
          if (!node || products.length >= 80) return;
          if (typeof node !== 'object') return;
          if (seenNodes.has(node)) return;
          seenNodes.add(node);

          const direct = maybeProduct(node);
          if (direct) products.push(direct);

          if (Array.isArray(node)) {
            node.forEach(walk);
            return;
          }
          Object.keys(node).slice(0, 250).forEach(key => walk(node[key]));
        }
        walk(root);
        const seen = {};
        return products.filter(item => {
          const key = (item.nav_id + '|' + item.name + '|' + item.unit + '|' + item.sp).toLowerCase();
          if (seen[key]) return false;
          seen[key] = true;
          return true;
        });
      }

      function looksLikeProductPayload(data) {
        try {
          const text = JSON.stringify(data).slice(0, 80000).toLowerCase();
          return (
            /product|cart_item|catalog|inventory|variant|merchant|price|mrp|display_name|product_name/.test(text) &&
            /price|mrp|selling|sp|inventory|availability|in_stock/.test(text)
          );
        } catch (_) {
          return false;
        }
      }

      function classifyText(text) {
        const lower = cleanText(text).toLowerCase();
        diag.challenge_detected = diag.challenge_detected || /captcha|challenge|access denied|blocked|unusual traffic|verify you are human/.test(lower);
        diag.location_gate_detected = diag.location_gate_detected || /set location|detect location|enter pincode|delivery location|location permission|not serviceable/.test(lower);
        diag.login_detected = diag.login_detected || /login|sign in|otp|mobile number/.test(lower);
      }

      function isCandidateProductUrl(url) {
        if (typeof url !== 'string') return false;
        return /blinkit|grofers/i.test(url) && /(search|product|listing|inventory|catalog|layout|feed|cart|merchant|variant|prn|v\\d+)/i.test(url);
      }

      function recordResponse(kind, method, url, status, contentType, text, durationMs) {
        const compact = compactUrl(url);
        diag.candidate_api_responses += 1;
        if (/json/i.test(contentType || '') || /^[\\[{]/.test(cleanText(text))) diag.json_responses += 1;
        if (/html/i.test(contentType || '') || /^</.test(cleanText(text))) diag.html_responses += 1;
        classifyText(text);

        const sample = {
          kind, method, url: compact, status, content_type: contentType || '',
          size: text ? text.length : 0, duration_ms: durationMs,
          preview: cleanText(text).slice(0, MAX_SAMPLE_TEXT)
        };
        diag.response_samples.push(sample);
        if (diag.response_samples.length > 12) diag.response_samples.shift();
        log('stage=first_response provider=blinkit method=' + method + ' status=' + status + ' content_type=' + (contentType || '') + ' size=' + sample.size + ' duration_ms=' + durationMs + ' url=' + compact);

        let data = null;
        try {
          data = JSON.parse(text);
          log('stage=parse provider=blinkit keys=' + Object.keys(data || {}).slice(0, 25).join(','));
        } catch (_) {}

        if (data && looksLikeProductPayload(data)) {
          diag.product_like_responses += 1;
          const products = collectProducts(data);
          diag.raw_product_objects += products.length;
          diag.product_samples = products.slice(0, 5).map(item => ({
            name: item.name, unit: item.unit, sp: item.sp, nav_id: item.nav_id
          }));
          if (products.length > 0) {
            diag.parsed_products = products.length;
            postSuccess({
              products,
              _debug: {
                provider: 'Blinkit',
                extraction: 'network',
                diagnostic: diag
              }
            });
          } else {
            log('stage=parser_regression provider=blinkit product_like_response=true parsed_products=0');
          }
        }
      }

      const originalFetch = window.fetch;
      window.fetch = async function(...args) {
        const request = args[0];
        const url = typeof request === 'string' ? request : (request && request.url) || '';
        const method = ((args[1] && args[1].method) || (request && request.method) || 'GET').toUpperCase();
        diag.fetch_count += 1;
        if (url && /blinkit|grofers/i.test(url)) {
          log('stage=search_request provider=blinkit transport=fetch method=' + method + ' url=' + compactUrl(url));
        }
        const started = Date.now();
        const response = await originalFetch.apply(this, args);
        if (isCandidateProductUrl(url)) {
          try {
            const text = await response.clone().text();
            recordResponse('fetch', method, url, response.status, response.headers && response.headers.get('content-type'), text, Date.now() - started);
          } catch (e) {
            log('stage=response_read_failed provider=blinkit transport=fetch message=' + cleanText(e && e.message));
          }
        }
        return response;
      };

      const XHR = window.XMLHttpRequest && window.XMLHttpRequest.prototype;
      if (XHR) {
        const originalOpen = XHR.open;
        const originalSend = XHR.send;
        XHR.open = function(method, url) {
          this.__tcMethod = method || 'GET';
          this.__tcUrl = url || '';
          return originalOpen.apply(this, arguments);
        };
        XHR.send = function() {
          const url = this.__tcUrl || '';
          const method = String(this.__tcMethod || 'GET').toUpperCase();
          const started = Date.now();
          diag.xhr_count += 1;
          if (url && /blinkit|grofers/i.test(url)) {
            log('stage=search_request provider=blinkit transport=xhr method=' + method + ' url=' + compactUrl(url));
          }
          this.addEventListener('load', function() {
            if (!isCandidateProductUrl(url)) return;
            try {
              recordResponse('xhr', method, url, this.status, this.getResponseHeader && this.getResponseHeader('content-type'), this.responseText || '', Date.now() - started);
            } catch (e) {
              log('stage=response_read_failed provider=blinkit transport=xhr message=' + cleanText(e && e.message));
            }
          });
          return originalSend.apply(this, arguments);
        };
      }

      Object.defineProperty(navigator, 'geolocation', {
        value: {
          getCurrentPosition: (success) => success({ coords: {
            latitude: ${latitude}, longitude: ${longitude}, accuracy: 10,
            altitude: null, altitudeAccuracy: null, heading: null, speed: null
          }, timestamp: Date.now() }),
          watchPosition: (success) => { success({ coords: {
            latitude: ${latitude}, longitude: ${longitude}, accuracy: 10,
            altitude: null, altitudeAccuracy: null, heading: null, speed: null
          }, timestamp: Date.now() }); return 0; },
          clearWatch: () => {}
        },
        configurable: true
      });

      try {
        localStorage.setItem('tc_last_blinkit_query', INPUT_QUERY);
        localStorage.setItem('tc_last_blinkit_lat', String(${latitude}));
        localStorage.setItem('tc_last_blinkit_lng', String(${longitude}));
      } catch (_) {}

      diag.query_sent_to_blinkit = location.href;
      log('stage=location_setup provider=blinkit input_query=' + INPUT_QUERY + ' encoded_query=' + ENCODED_QUERY + ' coordinates=${latitude},${longitude}');
    })();
    true;
  `;
}

const DOM_DIAGNOSTIC_INJECT = `
  (function() {
    const diag = window.__tcBlinkitDiag || {};
    const INPUT_QUERY = diag.input_query || '';
    const PRODUCT_WORDS = INPUT_QUERY.toLowerCase().split(/\\s+/).filter(Boolean);

    function post(type, payload) {
      try { window.ReactNativeWebView.postMessage(JSON.stringify({ type, payload })); } catch (_) {}
    }
    function postSuccess(payload) {
      diag.success_emitted = true;
      post('SEARCH_SUCCESS', payload);
    }
    function log(message) { post('LOG', message); }
    function cleanText(value) { return String(value || '').replace(/\\s+/g, ' ').trim(); }
    function priceFromText(text) {
      const match = cleanText(text).match(/(?:₹|Rs\\.?|INR)\\s*([0-9]+(?:\\.[0-9]+)?)/i);
      return match ? Number(match[1]) : null;
    }
    function queryRelevant(text) {
      const lower = cleanText(text).toLowerCase();
      return PRODUCT_WORDS.some(word => word.length > 2 && lower.includes(word));
    }
    function classifyText(text) {
      const lower = cleanText(text).toLowerCase();
      diag.challenge_detected = diag.challenge_detected || /captcha|challenge|access denied|blocked|unusual traffic|verify you are human/.test(lower);
      diag.location_gate_detected = diag.location_gate_detected || /set location|detect location|enter pincode|delivery location|location permission|not serviceable/.test(lower);
      diag.login_detected = diag.login_detected || /login|sign in|otp|mobile number/.test(lower);
    }
    function titleFromCard(card, text) {
      const candidates = Array.from(card.querySelectorAll('h1,h2,h3,h4,h5,h6,[data-testid],[data-test-id],span,div'))
        .map(el => cleanText(el.textContent))
        .filter(value =>
          value.length >= 4 &&
          value.length <= 140 &&
          !/(^add$|^buy$|^cart$|^search$|^sort|filter|delivery|mins?$)/i.test(value) &&
          !/(?:₹|Rs\\.?|INR)\\s*[0-9]/i.test(value)
        );
      return candidates.find(queryRelevant) || candidates[0] || '';
    }
    function extractDomProducts() {
      const selectors = [
        'a[href*="/prn/"]',
        'a[href*="/product"]',
        '[data-testid*="product" i]',
        '[data-test-id*="product" i]',
        '[class*="product" i]',
        '[class*="Product"]'
      ].join(',');
      const cards = Array.from(document.querySelectorAll(selectors));
      diag.dom_product_nodes = cards.length;
      let products = [];
      cards.forEach(card => {
        const text = cleanText(card.textContent);
        const price = priceFromText(text);
        const name = titleFromCard(card, text);
        if (!name || !price || !queryRelevant(name + ' ' + text)) return;
        const img = card.querySelector('img');
        const link = card.closest('a[href]') || card.querySelector('a[href]');
        const unitMatch = text.match(/\\b\\d+(?:\\.\\d+)?\\s*(?:ml|l|ltr|lt|g|kg|pc|pcs|pack)\\b/i);
        products.push({
          name,
          brand: name.toLowerCase().includes('amul') ? 'Amul' : 'Blinkit',
          sp: price,
          mrp: price,
          unit: unitMatch ? unitMatch[0] : '1 unit',
          img_url: img ? img.src : '',
          nav_id: link ? link.href : name,
          url: link ? link.href : '',
          source: 'blinkit_dom'
        });
      });
      const seen = {};
      products = products.filter(item => {
        const key = (item.nav_id + '|' + item.name + '|' + item.unit + '|' + item.sp).toLowerCase();
        if (seen[key]) return false;
        seen[key] = true;
        return true;
      }).slice(0, 40);
      if (products.length > 0) {
        diag.parsed_products = products.length;
        postSuccess({ products, _debug: { provider: 'Blinkit', extraction: 'dom', diagnostic: diag } });
        return true;
      }
      return false;
    }
    function emitFinalDiagnostic() {
      if (diag.success_emitted || diag.parsed_products > 0) return;
      const bodyText = cleanText(document.body && document.body.innerText);
      classifyText(bodyText);
      diag.final_url = location.href;
      diag.title = document.title;
      diag.body_chars = bodyText.length;
      diag.body_preview = bodyText.slice(0, 600);
      diag.result_container_count = document.querySelectorAll('main, [role="main"], [data-testid], [data-test-id], a[href*="/prn/"]').length;
      let code = 'BLINKIT_EMPTY_PROVIDER_RESPONSE';
      if (diag.challenge_detected) code = 'BLINKIT_CHALLENGE_PAGE';
      else if (diag.location_gate_detected) code = 'BLINKIT_LOCATION_FAILURE';
      else if (diag.product_like_responses > 0 && diag.parsed_products === 0) code = 'BLINKIT_PARSER_REGRESSION';
      else if (diag.dom_product_nodes > 0 && diag.parsed_products === 0 && bodyText.length > 1800) code = 'BLINKIT_DOM_SELECTOR_MISMATCH';
      else if ((diag.html_responses || 0) > 0 && !(diag.json_responses || 0)) code = 'BLINKIT_HTML_RESPONSE_NO_JSON';
      else if ((diag.candidate_api_responses || 0) === 0) code = 'BLINKIT_NO_CANDIDATE_API_RESPONSE';
      log('stage=debug_snapshot provider=blinkit code=' + code + ' snapshot=' + JSON.stringify(diag).slice(0, 4000));
      post('SEARCH_ERROR', { code, message: code + ' ' + JSON.stringify({
        input_query: diag.input_query,
        encoded_query: diag.encoded_query,
        query_sent_to_blinkit: diag.query_sent_to_blinkit,
        final_url: diag.final_url,
        title: diag.title,
        candidate_api_responses: diag.candidate_api_responses || 0,
        json_responses: diag.json_responses || 0,
        html_responses: diag.html_responses || 0,
        product_like_responses: diag.product_like_responses || 0,
        dom_product_nodes: diag.dom_product_nodes || 0,
        raw_product_objects: diag.raw_product_objects || 0,
        parsed_products: diag.parsed_products || 0,
        body_chars: diag.body_chars || 0,
        location: diag.location,
        response_samples: (diag.response_samples || []).slice(-5),
        product_samples: diag.product_samples || [],
        body_preview: diag.body_preview || ''
      }) });
    }
    if (!extractDomProducts()) {
      setTimeout(extractDomProducts, 1500);
      setTimeout(extractDomProducts, 3500);
      setTimeout(function() {
        if (!extractDomProducts()) emitFinalDiagnostic();
      }, 7000);
    }
  })();
  true;
`;

export default function BlinkitScraper({ query, latitude = 12.9716, longitude = 77.5946, onResults, onError }: ScraperProps) {
  const webViewRef = useRef<WebView>(null);
  const sentRef = useRef(false);
  const startedAtRef = useRef(0);
  const lastStageRef = useRef('idle');
  const lastFailureRef = useRef('');

  const injectedJavaScriptBeforeContentLoaded = useMemo(
    () => blinkitScript(query, latitude, longitude),
    [latitude, longitude, query],
  );

  useEffect(() => {
    if (!query) return;
    sentRef.current = false;
    lastFailureRef.current = '';
    startedAtRef.current = Date.now();
    lastStageRef.current = 'session_setup';
    console.log(`[BlinkitScraper] mounted query="${query}" location=${latitude},${longitude} stage=session_setup`);
    const timer = setTimeout(() => {
      if (!sentRef.current) {
        const totalMs = Date.now() - startedAtRef.current;
        const message = lastFailureRef.current || `BLINKIT_TIMEOUT Blinkit did not emit product data for "${query}"; last_stage=${lastStageRef.current}; total_ms=${totalMs}`;
        console.log('[BlinkitScraper]', message);
        onError(message);
      }
    }, 32000);
    return () => clearTimeout(timer);
  }, [latitude, longitude, onError, query]);

  const handleLoadEnd = () => {
    if (query) webViewRef.current?.injectJavaScript(DOM_DIAGNOSTIC_INJECT);
  };

  const onMessage = (event: any) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'LOG') {
        const payload = String(data.payload || '');
        const stage = payload.match(/stage=([a-z_]+)/)?.[1];
        if (stage) lastStageRef.current = stage;
        console.log('[BlinkitScraper] LOG:', payload);
      } else if (data.type === 'SEARCH_SUCCESS') {
        sentRef.current = true;
        lastStageRef.current = 'success';
        const count = Array.isArray(data.payload?.products) ? data.payload.products.length : 'raw';
        console.log(`[BlinkitScraper] SEARCH SUCCESS data received count=${count}`);
        onResults(data.payload);
      } else if (data.type === 'SEARCH_ERROR') {
        if (sentRef.current) return;
        const code = data.payload?.code || data.code || 'BLINKIT_PROVIDER_ERROR';
        const message = data.payload?.message || data.message || code;
        sentRef.current = true;
        lastFailureRef.current = message;
        lastStageRef.current = 'classified_failure';
        onError(message);
      }
    } catch (_) {}
  };

  return (
    <View style={styles.c}>
      <WebView
        ref={webViewRef}
        source={{ uri: `https://blinkit.com/s/?q=${encodeURIComponent(query)}` }}
        injectedJavaScriptBeforeContentLoaded={injectedJavaScriptBeforeContentLoaded}
        onMessage={onMessage}
        onLoadStart={() => {
          lastStageRef.current = 'navigation_start';
          console.log(`[BlinkitScraper] load start query="${query}" elapsed_ms=${Date.now() - startedAtRef.current}`);
        }}
        onLoadEnd={() => {
          lastStageRef.current = 'dom_ready';
          console.log(`[BlinkitScraper] load end query="${query}" elapsed_ms=${Date.now() - startedAtRef.current}`);
          handleLoadEnd();
        }}
        onError={event => {
          if (sentRef.current) return;
          const message = `BLINKIT_NETWORK_FAILURE ${event.nativeEvent.description || 'Blinkit WebView failed to load'}`;
          lastStageRef.current = 'network_failure';
          console.log('[BlinkitScraper] WebView error:', message);
          onError(message);
        }}
        onHttpError={event => {
          if (sentRef.current) return;
          const statusCode = event.nativeEvent.statusCode;
          const code = statusCode === 403 ? 'BLINKIT_HTTP_403' : statusCode === 429 ? 'BLINKIT_RATE_LIMITED' : 'BLINKIT_HTTP_ERROR';
          const message = `${code} status=${statusCode}`;
          lastStageRef.current = 'http_error';
          console.log('[BlinkitScraper] HTTP error:', message);
          onError(message);
        }}
        geolocationEnabled
        userAgent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
        javaScriptEnabled
        domStorageEnabled
        style={styles.h}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  c: { width: 390, height: 844, position: 'absolute', top: 0, left: 0, opacity: 0.01, overflow: 'hidden' },
  h: { width: 390, height: 844, opacity: 0.01 },
});
