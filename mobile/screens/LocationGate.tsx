import React, { useCallback, useState } from 'react';
import { Linking, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { AppHeader, Body, Card, Field, PrimaryButton, Screen, Title } from '../components/ui';
import { tc } from '../design/tokens';
import { UserLocation } from '../location/LocationContext';

export type { UserLocation } from '../location/LocationContext';

export default function LocationGate({ onLocationGranted }: { onLocationGranted: (location: UserLocation) => void }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [manual, setManual] = useState('');
  const requestLocation = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const permission = await Location.requestForegroundPermissionsAsync();
      if (permission.status !== 'granted') {
        setError('Location access was not granted. Enable it in system settings when you are ready.');
        return;
      }
      const position = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      const [place] = await Location.reverseGeocodeAsync(position.coords).catch(() => []);
      const city = place?.city || place?.subregion || undefined;
      const display = [place?.district, city, place?.postalCode].filter(Boolean).join(', ') || undefined;
      onLocationGranted({ latitude: position.coords.latitude, longitude: position.coords.longitude, city, display, postalCode: place?.postalCode || undefined, source: 'device' });
    } catch {
      setError('We could not read your location. Check Location Services and try again.');
    } finally {
      setLoading(false);
    }
  }, [onLocationGranted]);
  const useManualLocation = useCallback(async () => {
    if (manual.trim().length < 3) { setError('Enter an area, address or postal code.'); return; }
    setLoading(true); setError('');
    try {
      const [result] = await Location.geocodeAsync(manual.trim());
      if (!result) { setError('We could not resolve that location. Add a city or postal code and try again.'); return; }
      const [place] = await Location.reverseGeocodeAsync(result).catch(() => []);
      const city = place?.city || place?.subregion || undefined;
      const display = [place?.name, place?.district, city, place?.postalCode].filter(Boolean).join(', ') || manual.trim();
      onLocationGranted({ latitude: result.latitude, longitude: result.longitude, city, display, postalCode: place?.postalCode || undefined, source: 'manual' });
    } catch { setError('This address could not be resolved right now. Check your connection and try again.'); }
    finally { setLoading(false); }
  }, [manual, onLocationGranted]);

  return <Screen contentStyle={styles.content}>
    <AppHeader subtitle="Location and serviceability" />
    <View style={styles.heading}><View style={styles.heroIcon}><Feather name="map-pin" size={23} color={tc.color.iris} /></View><View style={styles.headingCopy}><Text style={styles.kicker}>SET YOUR LOCATION</Text><Title size="h1">Compare what is available near you.</Title></View></View>
    <Body muted style={styles.lede}>Choose a current or entered location. TrueCost never silently selects a city.</Body>
    <View style={styles.reasons}>
      <Feature icon="crosshair" title="Serviceability" />
      <Feature icon="clock" title="Delivery context" />
      <Feature icon="shield" title="Your control" />
    </View>
    {error ? <Card tone="danger" style={styles.error}><Body style={styles.errorText}>{error}</Body><PrimaryButton label="Open system settings" variant="outline" icon="settings" onPress={() => void Linking.openSettings()} /></Card> : null}
    <PrimaryButton label="Use my current location" icon="navigation" loading={loading} onPress={() => void requestLocation()} style={styles.cta} />
    <View style={styles.divider}><View style={styles.dividerLine} /><Body muted>or enter it yourself</Body><View style={styles.dividerLine} /></View>
    <Field label="Area, address or postal code" icon="search" value={manual} onChangeText={value => { setManual(value); setError(''); }} placeholder="e.g. Indiranagar, Bengaluru" returnKeyType="go" onSubmitEditing={() => void useManualLocation()} />
    <PrimaryButton label="Resolve this location" icon="map-pin" variant="outline" loading={loading} disabled={manual.trim().length < 3} onPress={() => void useManualLocation()} style={styles.manualCta} />
    <Body muted style={styles.note}>Foreground access is enough. TrueCost does not request background tracking.</Body>
  </Screen>;
}

function Feature({ icon, title }: { icon: React.ComponentProps<typeof Feather>['name']; title: string }) {
  return <View style={styles.feature}><View style={styles.featureIcon}><Feather name={icon} size={16} color={tc.color.iris} /></View><Text style={styles.featureTitle}>{title}</Text></View>;
}
const styles = StyleSheet.create({
  content: { paddingBottom: tc.space.xl }, heading: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 22 }, headingCopy: { flex: 1 }, heroIcon: { width: 52, height: 52, borderRadius: 18, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, kicker: { ...tc.type.eyebrow, color: tc.color.iris, marginBottom: 4 },
  lede: { fontSize: 14, marginTop: tc.space.sm }, reasons: { flexDirection: 'row', gap: 8, marginTop: 18 },
  feature: { flex: 1, minHeight: 82, borderRadius: tc.radius.md, borderWidth: 1, borderColor: tc.color.line, backgroundColor: tc.color.surface, padding: 9, alignItems: 'center', justifyContent: 'center' }, featureIcon: { width: 34, height: 34, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: tc.color.irisSoft }, featureTitle: { color: tc.color.inkSoft, fontSize: 9, lineHeight: 12, fontWeight: '700', textAlign: 'center', marginTop: 5 },
  error: { gap: tc.space.sm, marginTop: tc.space.md }, errorText: { color: tc.color.danger },
  cta: { marginTop: 18 }, divider: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm, marginVertical: 14 }, dividerLine: { flex: 1, height: 1, backgroundColor: tc.color.line }, manualCta: { marginTop: tc.space.sm }, note: { fontSize: 11, textAlign: 'center', marginTop: tc.space.md },
});
