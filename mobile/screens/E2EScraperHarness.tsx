import React, { useState, useEffect } from 'react';
import { View, Text } from 'react-native';
import { useRoute } from '@react-navigation/native';
import BlinkitScraper from '../components/scrapers/grocery/BlinkitScraper';
import ZeptoScraper from '../components/scrapers/grocery/ZeptoScraper';
import SwiggyInstamartScraper from '../components/scrapers/grocery/SwiggyInstamartScraper';
import BigBasketScraper from '../components/scrapers/grocery/BigBasketScraper';
import { sanitizeCapture, ScraperCertificationCaptureV1, validateScraperCertificationCaptureV1 } from '../lib/scraperCertification/sanitizeCapture';
import { documentDirectory, getInfoAsync, makeDirectoryAsync, writeAsStringAsync } from 'expo-file-system/legacy';
import { useAuth } from '../auth/AuthContext';

export default function E2EScraperHarness({ route: propRoute }: any) {
  const mockRoute = { params: { provider: 'blinkit', query: 'Red Bull Energy Drink 250 ml', caseId: 'common_redbull', domain: 'grocery', runId: 'blinkit_common_redbull' } };
  const route = propRoute?.params?.provider ? propRoute : mockRoute;
  const { provider, query, caseId, locationProfile, runId } = (route.params as any) || {};
  const [status, setStatus] = useState<string>('SCRAPER_CERT_LOADING');

  useEffect(() => {
    setStatus('SCRAPER_CERT_LOADING');
  }, [runId, query]);
  const { session } = useAuth();
  
  const scraperMap: Record<string, any> = {
    blinkit: BlinkitScraper,
    zepto: ZeptoScraper,
    swiggy: SwiggyInstamartScraper,
    swiggy_instamart: SwiggyInstamartScraper,
    bigbasket: BigBasketScraper
  };
  const Scraper = scraperMap[provider?.toLowerCase()];

  const testLat = process.env.EXPO_PUBLIC_TRUECOST_CERT_LOCATION_LAT;
  const testLng = process.env.EXPO_PUBLIC_TRUECOST_CERT_LOCATION_LON;
  const locationConfig = testLat && testLng ? { lat: parseFloat(testLat), lng: parseFloat(testLng), verified: true } : null;

  const handleResults = async (data: any) => {
    try {
      console.log('[ScraperHarness] LOG: Results received!', data ? typeof data : 'none');
      const certBackendUrl = process.env.EXPO_PUBLIC_CERT_BACKEND_URL || process.env.EXPO_PUBLIC_API_URL || 'http://10.0.2.2:8000';
      if (!certBackendUrl) {
        setStatus('SCRAPER_CERT_FAILED_CONFIGURATION');
        return;
      }
      
      const sanitized = sanitizeCapture(data);
      
      const envelope: ScraperCertificationCaptureV1 = {
        capture_version: 'truecost.scraper.capture.v1',
        run_id: runId || 'unknown_run',
        case_id: caseId || 'unknown_case',
        provider: provider,
        domain: route.params?.domain || 'grocery',
        query: query,
        captured_at: new Date().toISOString(),
        execution_mode: 'REAL_LIVE_SCRAPE',
        scraper_component: Scraper ? Scraper.name : 'UnknownScraper',
        message_type: 'SEARCH_SUCCESS',
        requested_location_profile: locationProfile || 'default',
        observed_location_evidence: locationConfig ? `lat:${locationConfig.lat},lng:${locationConfig.lng}` : 'NOT_AVAILABLE',
        location_verified: !!locationConfig,
        payload: sanitized
      };

      if (!validateScraperCertificationCaptureV1(envelope)) {
        setStatus('SCRAPER_CERT_FAILED_CONFIGURATION');
        return;
      }

      try {
        const dir = (documentDirectory || '') + 'scraper_captures/' + (runId || 'default') + '/';
        const dirInfo = await getInfoAsync(dir);
        if (!dirInfo.exists) {
          await makeDirectoryAsync(dir, { intermediates: true });
        }
        const fileUri = dir + provider + '_' + (caseId || 'unknown') + '_' + Date.now() + '.json';
        await writeAsStringAsync(fileUri, JSON.stringify(envelope));
      } catch (e) {
        setStatus('SCRAPER_CERT_FAILED');
        return;
      }

      const backendUrl = certBackendUrl + '/api/v1/aggregator';
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (session?.access_token) headers['Authorization'] = `Bearer ${session.access_token}`;

      console.log('[ScraperHarness] LOG: POSTing to', backendUrl + '/ingest');
      const res = await fetch(backendUrl + '/ingest', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          provider: provider,
          raw_data: sanitized,
          search_session_id: undefined,
          query: query,
          category: 'Grocery'
        })
      });

      if (!res.ok) {
        setStatus('SCRAPER_CERT_FAILED');
        return;
      }
      
      setStatus('SCRAPER_CERT_INGESTED');
    } catch (e) {
      setStatus('SCRAPER_CERT_FAILED');
    }
  };

  if (!Scraper) {
    return (
      <View style={{flex: 1, justifyContent: 'center', alignItems: 'center'}}>
        <Text testID="scraper-cert-status">SCRAPER_CERT_FAILED_CONFIGURATION</Text>
      </View>
    );
  }

  return (
    <View style={{flex: 1, justifyContent: 'center', alignItems: 'center'}}>
      <Text testID="scraper-cert-status">{status}</Text>
      <Scraper 
        key={route.params.runId || query}
        query={query || 'test'} 
        latitude={locationConfig?.lat} 
        longitude={locationConfig?.lng} 
        onResults={handleResults} 
        onError={() => setStatus('SCRAPER_CERT_FAILED')} 
      />
    </View>
  );
}
