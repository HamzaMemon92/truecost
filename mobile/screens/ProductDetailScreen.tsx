import React, { useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useAuth } from '../auth/AuthContext';
import { api } from '../api/client';
import { AppHeader, Body, Card, Chip, Eyebrow, PrimaryButton, ProviderLogo, Screen, SectionHeader, Title } from '../components/ui';
import { formatCurrency, tc } from '../design/tokens';
import { useQueryClient } from '../query/QueryClient';

type Offer = {
  provider?: string;
  price?: number;
  mrp?: number;
  delivery?: string;
  deliveryTime?: string;
  availability?: string;
  source_url?: string;
  deepLink?: string;
  observed_at?: string;
  payment_benefit?: string;
};

export default function ProductDetailScreen({ route, navigation }: any) {
  const { session, isGuest, updateSession } = useAuth();
  const cache = useQueryClient();
  const product = route.params?.product || {};
  const title = product.name || product.title || 'Product detail';
  const offers: Offer[] = Array.isArray(product.offers)
    ? product.offers
    : product.provider || product.price
      ? [{ provider: product.provider, price: product.price, source_url: product.source_url || product.deepLink, observed_at: product.observed_at }]
      : [];
  const bestObserved = useMemo(() => offers.filter(offer => Number.isFinite(offer.price)).sort((a, b) => (a.price || 0) - (b.price || 0))[0], [offers]);
  const observedPrice = bestObserved?.price ?? product.price ?? null;
  const [target, setTarget] = useState(observedPrice ? String(Math.floor(observedPrice * 0.9)) : '');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState('');
  const sourceUrl = bestObserved?.source_url || bestObserved?.deepLink || product.deepLink || product.source_url || null;

  const requireAccount = () => {
    setMessage('Sign in from Profile to save products and price watches.');
    return false;
  };

  const focusedCompare = () => navigation.navigate('FocusedCompare', {
    category: product.category || 'Shopping',
    color: product.category === 'Grocery' ? '#4CAF50' : tc.color.iris,
    query: title,
    initialQuery: title,
    product,
    focusProductId: product.id,
    provenance: 'product_detail_exact_compare',
  });

  const save = async () => {
    if (!session) return requireAccount();
    setBusy('save');
    setMessage('');
    try {
      await api(session, updateSession, '/commerce/saved-items', {
        method: 'POST',
        body: JSON.stringify({
          title,
          price: observedPrice,
          provider: bestObserved?.provider || product.provider || null,
          source_url: sourceUrl,
          metadata: { category: product.category, product_id: product.id, observed_at: bestObserved?.observed_at || product.observed_at },
        }),
      });
      cache.invalidate('saved');
      cache.invalidate('dashboard');
      setMessage('Saved successfully.');
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : 'Could not save right now.');
    } finally {
      setBusy('');
    }
  };

  const watch = async () => {
    const targetPrice = Number(target);
    if (!session) return requireAccount();
    if (!Number.isFinite(targetPrice) || targetPrice < 0) {
      setMessage('Enter a valid target price.');
      return;
    }
    setBusy('watch');
    setMessage('');
    try {
      await api(session, updateSession, '/commerce/price-watches', {
        method: 'POST',
        body: JSON.stringify({
          title,
          target_price: targetPrice,
          current_price: observedPrice,
          provider: bestObserved?.provider || product.provider || null,
          source_url: sourceUrl,
        }),
      });
      cache.invalidate('watches');
      cache.invalidate('dashboard');
      setMessage('Price alert created.');
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : 'Could not create this watch.');
    } finally {
      setBusy('');
    }
  };

  return <Screen>
    <AppHeader subtitle="Product intelligence" onBack={() => navigation.goBack()} />
    <View style={styles.top}>
      <View />
      <Pressable accessibilityRole="button" accessibilityLabel="Save product" style={styles.topAction} onPress={() => void save()}>
        <Feather name="bookmark" size={20} color={tc.color.iris} />
      </Pressable>
    </View>
    <Eyebrow style={styles.eyebrow}>PRODUCT INTELLIGENCE</Eyebrow>
    <Title size="h1">{title}</Title>
    {product.brand || product.category ? <View style={styles.tags}>
      {product.brand ? <Chip label={product.brand} /> : null}
      {product.category ? <Chip label={product.category} /> : null}
    </View> : null}

    <Card tone="iris" style={styles.hero}>
      <Text style={styles.heroLabel}>BEST OBSERVED ITEM PRICE</Text>
      <Text style={styles.price}>{formatCurrency(observedPrice, product.currency || 'INR')}</Text>
      <Body muted>{bestObserved?.provider || product.provider || 'No provider observation supplied'}</Body>
      <View style={styles.rule} />
      <Body muted>Fees, availability and payment eligibility are confirmed at provider checkout. This is not a price guarantee.</Body>
      <PrimaryButton label={offers.length > 1 ? 'Refresh exact comparison' : 'Find more prices for this model'} icon="search" onPress={focusedCompare} style={styles.focusedCta} />
    </Card>

    {offers.length ? <>
      <SectionHeader title={`Provider offers - ${offers.length}`} />
      {offers.map((offer, index) => {
        const meta = [offer.availability, offer.delivery || offer.deliveryTime].filter(Boolean).join(' - ') || 'Details confirmed at handoff';
        return <Pressable key={(offer.provider || 'offer') + index} style={({ pressed }) => [styles.offer, pressed && styles.pressed]} onPress={() => navigation.navigate('CheckoutHandoff', { product, offer })}>
          <ProviderLogo provider={offer.provider || 'Provider'} size="sm" />
          <View style={styles.offerCopy}>
            <Text style={styles.offerProvider}>{offer.provider || 'Provider'}</Text>
            <Text style={styles.offerMeta}>{meta}</Text>
            {offer.observed_at ? <Text style={styles.freshness}>Observed {new Date(offer.observed_at).toLocaleString()}</Text> : null}
          </View>
          <View style={styles.offerPrice}>
            <Text style={styles.offerValue}>{formatCurrency(offer.price, product.currency || 'INR')}</Text>
            <Feather name="chevron-right" size={18} color={tc.color.muted} />
          </View>
        </Pressable>;
      })}
    </> : <Card style={styles.noOffers}><Title size="h3">No provider offers supplied</Title><Body muted>Return to search to collect current provider observations.</Body></Card>}

    {product.specs && Object.keys(product.specs).length ? <>
      <SectionHeader title="Product specifications" />
      <Card>{Object.entries(product.specs).map(([key, value]) => <View key={key} style={styles.spec}><Text style={styles.specKey}>{key}</Text><Text style={styles.specValue}>{String(value)}</Text></View>)}</Card>
    </> : null}

    <SectionHeader title="Price intelligence" />
    <Card tone="mint">
      <Title size="h3">Set a target price</Title>
      <Body muted style={styles.watchBody}>The target is stored against future observed prices.</Body>
      {observedPrice ? <Body muted style={styles.prefill}>Pre-filled at 10% below the current observed price of {formatCurrency(observedPrice)}</Body> : null}
      <View style={styles.target}>
        <Text style={styles.rupee}>Rs</Text>
        <TextInput accessibilityLabel="Target price" keyboardType="decimal-pad" value={target} onChangeText={setTarget} placeholder="Target price" placeholderTextColor={tc.color.muted} style={styles.targetInput} />
      </View>
      <PrimaryButton label="Create price watch" variant="mint" icon="bell" loading={busy === 'watch'} onPress={() => void watch()} style={styles.watchAction} />
    </Card>

    {Array.isArray(product.observations) ? <PrimaryButton label="View price history" variant="outline" icon="trending-down" onPress={() => navigation.navigate('PriceTrends', { product, observations: product.observations })} style={styles.secondary} /> : null}
    {offers.length > 1 ? <PrimaryButton label="Compare offers" variant="outline" icon="columns" onPress={() => navigation.navigate('Comparison', { title, options: offers, product })} style={styles.secondary} /> : null}
    {message ? <Card tone={message.includes('success') || message.includes('created') ? 'mint' : isGuest ? 'iris' : 'danger'} style={styles.message}><Body style={styles.messageText}>{message}</Body></Card> : null}
  </Screen>;
}

const styles = StyleSheet.create({
  top: { height: 0, flexDirection: 'row', justifyContent: 'space-between', zIndex: 2 },
  topAction: { width: 44, height: 44, marginTop: 7, borderRadius: tc.radius.sm, backgroundColor: tc.color.surface, borderWidth: 1, borderColor: tc.color.line, alignItems: 'center', justifyContent: 'center' },
  eyebrow: { marginTop: tc.space.lg, marginBottom: tc.space.xs },
  tags: { flexDirection: 'row', flexWrap: 'wrap', gap: tc.space.xs, marginTop: tc.space.md },
  hero: { marginTop: tc.space.lg },
  heroLabel: { ...tc.type.eyebrow, color: tc.color.iris },
  price: { ...tc.type.price, fontSize: 34, color: tc.color.ink, marginTop: 5 },
  rule: { height: 1, backgroundColor: '#DAD2FF', marginVertical: tc.space.md },
  focusedCta: { marginTop: tc.space.md },
  offer: { minHeight: 76, flexDirection: 'row', alignItems: 'center', gap: tc.space.sm, paddingVertical: tc.space.sm, borderBottomWidth: 1, borderBottomColor: tc.color.line },
  offerCopy: { flex: 1 },
  offerProvider: { ...tc.type.h3, color: tc.color.ink },
  offerMeta: { ...tc.type.bodySmall, color: tc.color.muted },
  freshness: { ...tc.type.bodySmall, fontSize: 11, color: tc.color.mint, marginTop: 2 },
  offerPrice: { alignItems: 'center', flexDirection: 'row', gap: tc.space.xs },
  offerValue: { ...tc.type.h3, color: tc.color.ink, fontVariant: ['tabular-nums'] },
  pressed: { opacity: 0.72 },
  noOffers: { marginTop: tc.space.lg, gap: 3 },
  spec: { minHeight: 46, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: tc.color.line, gap: tc.space.md },
  specKey: { ...tc.type.bodySmall, color: tc.color.muted, flex: 1, textTransform: 'capitalize' },
  specValue: { ...tc.type.label, color: tc.color.ink, flex: 1, textAlign: 'right' },
  watchBody: { marginTop: 3 },
  prefill: { fontSize: 11, marginTop: 2, color: tc.color.mint },
  target: { height: 52, borderRadius: tc.radius.md, backgroundColor: tc.color.surface, borderWidth: 1, borderColor: '#BDE8D9', flexDirection: 'row', alignItems: 'center', paddingHorizontal: tc.space.md, marginTop: tc.space.md },
  rupee: { ...tc.type.h3, color: tc.color.mint },
  targetInput: { flex: 1, minHeight: 50, color: tc.color.ink, fontSize: 16, marginLeft: 4 },
  watchAction: { marginTop: tc.space.sm },
  secondary: { marginTop: tc.space.sm },
  message: { marginTop: tc.space.md },
  messageText: { color: tc.color.ink },
});
