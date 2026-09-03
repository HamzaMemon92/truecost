import React, { useState } from 'react';
import { StyleSheet, Text } from 'react-native';
import { HotelSearchRequest, searchHotels } from '../api/travel';
import { ProviderHealthPanel } from '../components/ProviderHealthPanel';
import { AppHeader, Body, Card, Field, PrimaryButton, Screen, SectionHeader } from '../components/ui';
import { CategoryHero, SelectionRow } from '../features/categories/components';
import { tc } from '../design/tokens';

const budgets: Record<string, number | undefined> = { 'Any budget': undefined, 'Up to ₹3k': 3000, 'Up to ₹7k': 7000, 'Up to ₹15k': 15000 };
const ratings: Record<string, number | undefined> = { 'Any rating': undefined, '3+': 3, '4+': 4, '5 star': 5 };
const isoDate = /^\d{4}-\d{2}-\d{2}$/;

export default function HotelsScreen({ navigation, route }: any) {
  const [destination, setDestination] = useState(route.params?.initialQuery || ''); const [checkIn, setCheckIn] = useState(''); const [checkOut, setCheckOut] = useState(''); const [guests, setGuests] = useState('2'); const [rooms, setRooms] = useState('1'); const [budget, setBudget] = useState('Any budget'); const [rating, setRating] = useState('Any rating'); const [filter, setFilter] = useState('Best value');
  const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const compare = async () => {
    if (destination.trim().length < 2) return setError('Enter a destination or property area.');
    if (!isoDate.test(checkIn) || !isoDate.test(checkOut)) return setError('Use YYYY-MM-DD for check-in and check-out.');
    if (checkOut <= checkIn) return setError('Check-out must be after check-in.');
    setLoading(true); setError('');
    try {
      const request: HotelSearchRequest = { destination: destination.trim(), checkin_date: checkIn, checkout_date: checkOut, guests: Number(guests), rooms: Number(rooms), budget_max: budgets[budget], star_rating_min: ratings[rating] };
      const result = await searchHotels(request);
      navigation.navigate('HotelResults', { result, filter });
    } catch (next) { setError(next instanceof Error ? next.message : 'Verified hotel inventory is not available right now.'); }
    finally { setLoading(false); }
  };
  return <Screen>
    <AppHeader
      title="Hotels TrueCost"
      subtitle="Compare room rates & verified inventory"
      onBack={() => navigation.goBack()}
      onNotifications={() => navigation.navigate('Notifications')}
      onProfile={() => navigation.navigate('Profile')}
    />
    <CategoryHero eyebrow="HOTELS / STAY SETUP" title="Find the stay that fits the whole trip." body="Search verified room inventory when a stay provider is available. TrueCost never invents a room price." icon="home" />
    <ProviderHealthPanel categoryId="hotels" title="Stay provider readiness" />
    <Card tone="iris" style={styles.form}><Field label="Destination or property area" value={destination} onChangeText={value => { setDestination(value); setError(''); }} icon="map-pin" /><Field label="Check-in (YYYY-MM-DD)" value={checkIn} onChangeText={value => { setCheckIn(value); setError(''); }} icon="calendar" containerStyle={styles.field} /><Field label="Check-out (YYYY-MM-DD)" value={checkOut} onChangeText={value => { setCheckOut(value); setError(''); }} icon="calendar" containerStyle={styles.field} />{error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}</Card>
    <SectionHeader title="Guests" /><SelectionRow values={['1', '2', '3', '4']} selected={guests} onSelect={setGuests} />
    <SectionHeader title="Rooms" /><SelectionRow values={['1', '2', '3']} selected={rooms} onSelect={setRooms} />
    <SectionHeader title="Maximum nightly room total" /><SelectionRow values={Object.keys(budgets)} selected={budget} onSelect={setBudget} />
    <SectionHeader title="Minimum star rating" /><SelectionRow values={Object.keys(ratings)} selected={rating} onSelect={setRating} />
    <SectionHeader title="Results view" /><SelectionRow values={['Best value', 'Cheapest', 'Refundable']} selected={filter} onSelect={setFilter} />
    <Body muted style={styles.note}>Results view is a presentation filter. The backend remains authoritative for its supplied recommendation.</Body>
    <Card style={styles.map}><Text style={styles.mapTitle}>Map view</Text><Body muted>The current HotelOption contract has no coordinates, so map markers remain disabled rather than invented.</Body></Card>
    <PrimaryButton label="Search verified stays" icon="arrow-right" loading={loading} onPress={() => void compare()} style={styles.cta} />
  </Screen>;
}
const styles = StyleSheet.create({ form: { marginTop: tc.space.lg }, field: { marginTop: tc.space.sm }, error: { ...tc.type.bodySmall, color: tc.color.danger, marginTop: tc.space.sm }, note: { marginTop: tc.space.xs }, map: { marginTop: tc.space.lg }, mapTitle: { ...tc.type.label, color: tc.color.ink, marginBottom: 4 }, cta: { marginTop: tc.space.lg } });
