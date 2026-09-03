import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { AppHeader, Body, Card, Chip, PrimaryButton, Screen, SectionHeader, Title } from '../components/ui';
import { SystemState } from '../components/SystemState';
import { formatCurrency, tc } from '../design/tokens';
import { useUserLocation } from '../location/LocationContext';
import { useQueryClient } from '../query/QueryClient';
import { useApiQuery } from '../query/useApiQuery';
import type { Profile } from '../types/personalization';

type CartItem = { id: string; title: string; quantity: number; unit_price: number | null; provider: string | null; source_url: string | null; metadata: Record<string, unknown> };
type Cart = { id: string; name: string; currency: string; item_count: number; estimated_total: number; items: CartItem[] };
type Objective = 'cheapest' | 'balanced' | 'fastest';

export default function SmartCartScreen({ navigation }: any) {
  const { session, isGuest, updateSession } = useAuth(); const { location } = useUserLocation();
  const cache = useQueryClient(); const [objective, setObjective] = useState<Objective>('balanced'); const [busyId, setBusyId] = useState(''); const [creating, setCreating] = useState(false);
  const { data: carts, loading, error, refetch } = useApiQuery<Cart[]>('carts', '/commerce/carts', { enabled: !!session, maxAge: 5_000 });
  const { data: profile } = useApiQuery<Profile>('profile', '/profiles/me', { enabled: !!session, maxAge: 20_000 });
  useEffect(() => { if (profile?.preferences.objective) setObjective(profile.preferences.objective); }, [profile?.preferences.objective]);
  const cart = carts?.[0];
  const reload = async () => { cache.invalidate('carts'); cache.invalidate('dashboard'); await refetch(); };
  const create = async () => {
    if (!session) return; setCreating(true);
    try { await api(session, updateSession, '/commerce/carts', { method: 'POST', body: JSON.stringify({ name: 'My grocery basket', currency: 'INR' }) }); await reload(); }
    finally { setCreating(false); }
  };
  const changeQuantity = async (item: CartItem, quantity: number) => {
    if (!session || !cart || quantity < 1) return; setBusyId(item.id);
    try { await api(session, updateSession, '/commerce/carts/' + cart.id + '/items/' + item.id, { method: 'PATCH', body: JSON.stringify({ title: item.title, quantity, unit_price: item.unit_price, provider: item.provider, source_url: item.source_url, metadata: item.metadata || {} }) }); await reload(); }
    finally { setBusyId(''); }
  };
  const remove = async (item: CartItem) => {
    if (!session || !cart) return; setBusyId(item.id);
    try { await api(session, updateSession, '/commerce/carts/' + cart.id + '/items/' + item.id, { method: 'DELETE' }); await reload(); }
    finally { setBusyId(''); }
  };
  const compare = () => { if (cart?.items.length) navigation.navigate('CartOptimization', { cart, objective }); };
  return <Screen>
    <AppHeader subtitle="Grocery basket builder" onBack={() => navigation.goBack()} onNotifications={() => navigation.navigate('Notifications')} />
    <Text style={styles.kicker}>GROCERY / SMART CART</Text><Title size="h1" style={styles.title}>{cart?.name || 'Build one clear basket.'}</Title>
    <Body muted>{cart ? 'Edit quantities, substitution permission and the decision objective before comparing again.' : 'Add observed products to compare a complete basket instead of isolated prices.'}</Body>
    {!session && isGuest ? <Card tone="iris" style={styles.guest}><Title size="h3">Sign in to persist a cart</Title><Body muted>Guest search remains available, but carts need a TrueCost account.</Body><PrimaryButton label="Open Profile to sign in" variant="outline" onPress={() => navigation.navigate('MainTabs', { screen: 'Profile' })} /></Card> : null}
    {session && loading && !cart ? <SystemState kind="loading" /> : null}
    {session && error ? <SystemState kind="offline" actionLabel="Try again" onAction={() => void refetch()} /> : null}
    {session && !loading && !cart ? <SystemState kind="empty_cart" actionLabel="Create a basket" onAction={() => void create()} /> : null}
    {creating ? <SystemState kind="loading" compact /> : null}
    {cart ? <>
      <Card tone="mint" style={styles.summary}><View><Text style={styles.label}>OBSERVED ITEM TOTAL</Text><Text style={styles.total}>{formatCurrency(cart.estimated_total, cart.currency)}</Text><Body muted>{cart.item_count} total units. Provider fees are not included unless returned by the provider.</Body></View></Card>
      <SectionHeader title="Decision objective" />
      <View style={styles.objectives}>{(['cheapest', 'balanced', 'fastest'] as Objective[]).map(value => <Chip key={value} label={value[0].toUpperCase() + value.slice(1)} selected={objective === value} onPress={() => setObjective(value)} />)}</View>
      <SectionHeader title={'Basket items · ' + cart.item_count} />
      <View style={styles.items}>{cart.items.map(item => <Card key={item.id} style={styles.item}>
        <View style={styles.itemTop}><View style={styles.itemCopy}><Text style={styles.itemTitle}>{item.title}</Text><Text style={styles.itemMeta}>{item.provider || 'Provider not selected'} · {formatCurrency(item.unit_price, cart.currency)} each</Text></View><Pressable accessibilityRole="button" accessibilityLabel={'Remove ' + item.title} disabled={busyId === item.id} onPress={() => void remove(item)} style={styles.remove}><Feather name="trash-2" size={18} color={tc.color.danger} /></Pressable></View>
        <View style={styles.quantity}><Pressable accessibilityRole="button" accessibilityLabel={'Decrease ' + item.title} disabled={item.quantity <= 1 || busyId === item.id} onPress={() => void changeQuantity(item, item.quantity - 1)} style={[styles.quantityButton, item.quantity <= 1 && styles.disabled]}><Feather name="minus" size={17} color={tc.color.ink} /></Pressable><Text accessibilityLabel={'Quantity ' + item.quantity} style={styles.quantityValue}>{item.quantity}</Text><Pressable accessibilityRole="button" accessibilityLabel={'Increase ' + item.title} disabled={busyId === item.id} onPress={() => void changeQuantity(item, item.quantity + 1)} style={styles.quantityButton}><Feather name="plus" size={17} color={tc.color.ink} /></Pressable><View style={styles.itemSubtotal}><Text style={styles.itemSubtotalLabel}>Subtotal</Text><Text style={styles.itemSubtotalValue}>{formatCurrency((item.unit_price || 0) * item.quantity, cart.currency)}</Text></View></View>
      </Card>)}</View>
      {!cart.items.length ? <SystemState kind="empty_cart" actionLabel="Search groceries" onAction={() => navigation.navigate('GroceryHub')} /> : <>
        <PrimaryButton label="Review substitutions" variant="outline" icon="repeat" onPress={() => navigation.navigate('Substitutions', { cart })} style={styles.secondary} />
        <PrimaryButton label="Calculate optimized basket" icon="cpu" onPress={compare} style={styles.primary} />
      </>}
    </> : null}
  </Screen>;
}
const styles = StyleSheet.create({
  kicker: { ...tc.type.eyebrow, color: tc.color.iris, marginTop: tc.space.md }, title: { marginTop: 3, marginBottom: tc.space.xs }, guest: { marginTop: tc.space.lg, gap: tc.space.sm }, summary: { marginTop: tc.space.lg },
  label: { ...tc.type.eyebrow, color: tc.color.mint }, total: { ...tc.type.price, color: tc.color.ink, marginVertical: 4 },
  objectives: { flexDirection: 'row', flexWrap: 'wrap', gap: tc.space.xs }, items: { gap: tc.space.sm }, item: { padding: tc.space.md },
  itemTop: { flexDirection: 'row', alignItems: 'flex-start', gap: tc.space.sm }, itemCopy: { flex: 1 }, itemTitle: { ...tc.type.h3, color: tc.color.ink }, itemMeta: { ...tc.type.bodySmall, color: tc.color.muted, marginTop: 3 },
  remove: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' }, quantity: { flexDirection: 'row', alignItems: 'center', marginTop: tc.space.md, gap: tc.space.xs },
  quantityButton: { width: 44, height: 44, borderRadius: 15, backgroundColor: tc.color.surfaceMuted, alignItems: 'center', justifyContent: 'center' }, quantityValue: { ...tc.type.h3, minWidth: 32, textAlign: 'center', color: tc.color.ink, fontVariant: ['tabular-nums'] },
  itemSubtotal: { marginLeft: 'auto', alignItems: 'flex-end' }, itemSubtotalLabel: { ...tc.type.bodySmall, fontSize: 11, color: tc.color.muted }, itemSubtotalValue: { ...tc.type.label, color: tc.color.ink, fontVariant: ['tabular-nums'] },
  disabled: { opacity: 0.35 }, secondary: { marginTop: tc.space.sm }, primary: { marginTop: tc.space.md },
});
