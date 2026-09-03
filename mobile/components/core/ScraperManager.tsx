import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import type { UserLocation } from '../../screens/LocationGate';

// Grocery (4)
import ZeptoScraper from '../scrapers/grocery/ZeptoScraper';
import BlinkitScraper from '../scrapers/grocery/BlinkitScraper';
import SwiggyInstamartScraper from '../scrapers/grocery/SwiggyInstamartScraper';
import BigBasketScraper from '../scrapers/grocery/BigBasketScraper';
// Mobility (4)
import UberScraper from '../scrapers/mobility/UberScraper';
import OlaScraper from '../scrapers/mobility/OlaScraper';
import RapidoScraper from '../scrapers/mobility/RapidoScraper';
import NammaYatriScraper from '../scrapers/mobility/NammaYatriScraper';
// Shopping (4)
import AmazonScraper from '../scrapers/shopping/AmazonScraper';
import FlipkartScraper from '../scrapers/shopping/FlipkartScraper';
import MeeshoScraper from '../scrapers/shopping/MeeshoScraper';
import MyntraScraper from '../scrapers/shopping/MyntraScraper';
// Food (4)
import SwiggyFoodScraper from '../scrapers/food/SwiggyFoodScraper';
import ZomatoScraper from '../scrapers/food/ZomatoScraper';
import MagicPinScraper from '../scrapers/food/MagicPinScraper';
import EatSureScraper from '../scrapers/food/EatSureScraper';
// Pharmacy (4)
import Tata1mgScraper from '../scrapers/pharmacy/Tata1mgScraper';
import PharmEasyScraper from '../scrapers/pharmacy/PharmEasyScraper';
import Apollo247Scraper from '../scrapers/pharmacy/Apollo247Scraper';
import NetmedsScraper from '../scrapers/pharmacy/NetmedsScraper';
// Travel (4)
import MakeMyTripScraper from '../scrapers/travel/MakeMyTripScraper';
import GoibiboScraper from '../scrapers/travel/GoibiboScraper';
import IxigoScraper from '../scrapers/travel/IxigoScraper';
import CleartripScraper from '../scrapers/travel/CleartripScraper';
// Finance (4)
import BankBazaarScraper from '../scrapers/finance/BankBazaarScraper';
import PolicyBazaarScraper from '../scrapers/finance/PolicyBazaarScraper';
import PaisaBazaarScraper from '../scrapers/finance/PaisaBazaarScraper';
import CreditMantriScraper from '../scrapers/finance/CreditMantriScraper';
// Productivity (4)
import NotionScraper from '../scrapers/productivity/NotionScraper';
import FigmaScraper from '../scrapers/productivity/FigmaScraper';
import SlackScraper from '../scrapers/productivity/SlackScraper';
import CanvaScraper from '../scrapers/productivity/CanvaScraper';

interface ScraperManagerProps {
  category: string;
  query: string;
  userLocation?: UserLocation;
  onResults: (provider: string, data: any) => void;
  onError: (provider: string, error: string) => void;
}

export default function ScraperManager({
  category, query, userLocation, onResults, onError,
}: ScraperManagerProps) {
  // Route query only to the active category; others stay pre-warmed but silent
  const q  = (cat: string) => category === cat ? query : '';
  const r  = (p: string)   => (d: any)    => onResults(p, d);
  const e  = (p: string)   => (err: string) => onError(p, err);

  const lat = userLocation?.latitude  ?? 12.9716;  // Bengaluru default
  const lng = userLocation?.longitude ?? 77.5946;

  useEffect(() => {
    console.log(
      `[ScraperManager] ${category} search location: ${lat},${lng}` +
      (userLocation?.postalCode ? ` pincode=${userLocation.postalCode}` : '') +
      (userLocation?.display ? ` display="${userLocation.display}"` : '')
    );
  }, [category, lat, lng, userLocation?.display, userLocation?.postalCode]);

  return (
    <View style={styles.container}>
      {/* GROCERY */}
      {category === 'Grocery' && (
        <>
          <ZeptoScraper           query={query} latitude={lat} longitude={lng} onResults={r('Zepto')} onError={e('Zepto')} />
          <BlinkitScraper         query={query} latitude={lat} longitude={lng} onResults={r('Blinkit')} onError={e('Blinkit')} />
          <SwiggyInstamartScraper query={query} latitude={lat} longitude={lng} onResults={r('Swiggy')} onError={e('Swiggy')} />
          <BigBasketScraper       query={query} latitude={lat} longitude={lng} onResults={r('Bigbasket')} onError={e('Bigbasket')} />
        </>
      )}

      {/* MOBILITY */}
      {category === 'Mobility' && (
        <>
          <UberScraper            query={query} latitude={lat} longitude={lng} onResults={r('Uber')} onError={e('Uber')} />
          <OlaScraper             query={query} latitude={lat} longitude={lng} onResults={r('Ola')} onError={e('Ola')} />
          <RapidoScraper          query={query} latitude={lat} longitude={lng} onResults={r('Rapido')} onError={e('Rapido')} />
          <NammaYatriScraper      query={query} onResults={r('Namma Yatri')} onError={e('Namma Yatri')} />
        </>
      )}

      {/* SHOPPING */}
      {category === 'Shopping' && (
        <>
          <AmazonScraper          query={query} onResults={r('Amazon')} onError={e('Amazon')} />
          <FlipkartScraper        query={query} onResults={r('Flipkart')} onError={e('Flipkart')} />
          <MeeshoScraper          query={query} onResults={r('Meesho')} onError={e('Meesho')} />
          <MyntraScraper          query={query} onResults={r('Myntra')} onError={e('Myntra')} />
        </>
      )}

      {/* FOOD */}
      {category === 'Food' && (
        <>
          <SwiggyFoodScraper      query={query} latitude={lat} longitude={lng} onResults={r('Swiggy Food')} onError={e('Swiggy Food')} />
          <ZomatoScraper          query={query} latitude={lat} longitude={lng} onResults={r('Zomato')} onError={e('Zomato')} />
          <MagicPinScraper        query={query} onResults={r('MagicPin')} onError={e('MagicPin')} />
          <EatSureScraper         query={query} onResults={r('EatSure')} onError={e('EatSure')} />
        </>
      )}

      {/* PHARMACY */}
      {category === 'Pharmacy' && (
        <>
          <Tata1mgScraper         query={query} onResults={r('Tata 1mg')} onError={e('Tata 1mg')} />
          <PharmEasyScraper       query={query} onResults={r('PharmEasy')} onError={e('PharmEasy')} />
          <Apollo247Scraper       query={query} onResults={r('Apollo 247')} onError={e('Apollo 247')} />
          <NetmedsScraper         query={query} onResults={r('Netmeds')} onError={e('Netmeds')} />
        </>
      )}

      {/* TRAVEL */}
      {category === 'Travel' && (
        <>
          <MakeMyTripScraper      query={query} onResults={r('MakeMyTrip')} onError={e('MakeMyTrip')} />
          <GoibiboScraper         query={query} onResults={r('Goibibo')} onError={e('Goibibo')} />
          <IxigoScraper           query={query} onResults={r('Ixigo')} onError={e('Ixigo')} />
          <CleartripScraper       query={query} onResults={r('Cleartrip')} onError={e('Cleartrip')} />
        </>
      )}

      {/* FINANCE */}
      {category === 'Finance' && (
        <>
          <BankBazaarScraper      query={query} onResults={r('BankBazaar')} onError={e('BankBazaar')} />
          <PolicyBazaarScraper    query={query} onResults={r('PolicyBazaar')} onError={e('PolicyBazaar')} />
          <PaisaBazaarScraper     query={query} onResults={r('PaisaBazaar')} onError={e('PaisaBazaar')} />
          <CreditMantriScraper    query={query} onResults={r('CreditMantri')} onError={e('CreditMantri')} />
        </>
      )}

      {/* PRODUCTIVITY */}
      {category === 'Productivity' && (
        <>
          <NotionScraper          query={query} onResults={r('Notion')} onError={e('Notion')} />
          <FigmaScraper           query={query} onResults={r('Figma')} onError={e('Figma')} />
          <SlackScraper           query={query} onResults={r('Slack')} onError={e('Slack')} />
          <CanvaScraper           query={query} onResults={r('Canva')} onError={e('Canva')} />
        </>
      )}
    </View>
  );
}


const styles = StyleSheet.create({
  container: {
    width: 390,
    height: 844,
    position: 'absolute',
    top: -1200,
    left: -1200,
    opacity: 0.01,
    pointerEvents: 'none',
  },
});
