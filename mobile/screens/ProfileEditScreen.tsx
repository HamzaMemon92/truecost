import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { CATEGORY_CATALOG } from '../catalog/categories';
import { RetentionHeader } from '../components/RetentionPrimitives';
import { Body, Card, Chip, Field, PrimaryButton, Screen, SectionHeader } from '../components/ui';
import { SystemState } from '../components/SystemState';
import { tc } from '../design/tokens';
import { useApiQuery } from '../query/useApiQuery';
import { useQueryClient } from '../query/QueryClient';
import type { Profile } from '../types/personalization';

export default function ProfileEditScreen({ navigation }: { navigation: any }) {
  const { session, updateSession } = useAuth(); const cache = useQueryClient(); const profile = useApiQuery<Profile>('profile', '/profiles/me', { maxAge: 6_000 });
  const [name, setName] = useState(''); const [language, setLanguage] = useState('en'); const [region, setRegion] = useState('IN'); const [currency, setCurrency] = useState('INR'); const [categories, setCategories] = useState<string[]>([]); const [saving, setSaving] = useState(false); const [message, setMessage] = useState('');
  useEffect(() => { if (!profile.data) return; setName(profile.data.display_name || ''); setLanguage(profile.data.preferences.language || 'en'); setRegion(profile.data.preferences.region || 'IN'); setCurrency(profile.data.preferences.currency || 'INR'); setCategories(profile.data.preferences.preferred_categories || []); }, [profile.data]);
  const toggleCategory = (value: string) => setCategories(current => current.includes(value) ? current.filter(item => item !== value) : [...current, value]);
  const save = async () => { if (!session) return; setSaving(true); setMessage(''); try { await api(session, updateSession, '/profiles/me', { method: 'PUT', body: JSON.stringify({ display_name: name.trim() || null }) }); await api(session, updateSession, '/profiles/me/preferences', { method: 'PATCH', body: JSON.stringify({ preferred_categories: categories, language: language.trim() || 'en', region: region.trim().toUpperCase() || 'IN', currency: currency.trim().toUpperCase() || 'INR' }) }); cache.invalidate('profile'); setMessage('Profile updated.'); await profile.refetch(); } catch (error) { setMessage(error instanceof Error ? error.message : 'Profile could not be updated.'); } finally { setSaving(false); } };
  if (profile.loading && !profile.data) return <Screen><SystemState kind="loading" /></Screen>;
  if (!profile.data) return <Screen><SystemState kind="offline" actionLabel="Try again" onAction={() => void profile.refetch()} /></Screen>;
  return <Screen><RetentionHeader eyebrow="TrueCost identity" title="Edit profile" subtitle="Keep personal details minimal and preference data purposeful." onBack={() => navigation.goBack()} />
    <Card tone="iris" style={styles.identity}><View style={styles.avatar}><Text style={styles.initial}>{(name || profile.data.email || profile.data.phone_number || 'T').charAt(0).toUpperCase()}</Text></View><View style={styles.identityCopy}><Text style={styles.email}>{profile.data.email || profile.data.phone_number || 'Verified TrueCost account'}</Text><Body muted>Your sign-in identifier is read-only in this version.</Body></View></Card>
    <SectionHeader title="How TrueCost addresses you" /><Field label="Display name" value={name} onChangeText={setName} placeholder="Your preferred name" textContentType="name" autoComplete="name" />
    <SectionHeader title="Regional preferences" /><View style={styles.fieldRow}><Field label="Language" value={language} onChangeText={setLanguage} placeholder="en" containerStyle={styles.field} /><Field label="Region" value={region} onChangeText={setRegion} autoCapitalize="characters" maxLength={2} containerStyle={styles.field} /><Field label="Currency" value={currency} onChangeText={setCurrency} autoCapitalize="characters" maxLength={3} containerStyle={styles.field} /></View>
    <SectionHeader title="Category interests" /><Body muted>These interests can order discovery; they never hide the full category catalog.</Body><View style={styles.chips}>{CATEGORY_CATALOG.map(item => <Chip key={item.id} label={item.name} selected={categories.includes(item.name)} onPress={() => toggleCategory(item.name)} />)}</View>
    <Card tone="mint" style={styles.privacy}><Feather name="shield" size={19} color={tc.color.mint} /><Body style={styles.privacyText}>TrueCost does not request date of birth, gender, full payment credentials or other information that is unnecessary for comparisons.</Body></Card>
    <PrimaryButton label="Save profile" icon="check" loading={saving} onPress={() => void save()} style={styles.save} />{message ? <Text accessibilityRole="alert" style={[styles.message, message === 'Profile updated.' && styles.success]}>{message}</Text> : null}
  </Screen>;
}
const styles = StyleSheet.create({ identity: { flexDirection: 'row', alignItems: 'center', gap: tc.space.md }, avatar: { width: 58, height: 58, borderRadius: 20, backgroundColor: tc.color.iris, alignItems: 'center', justifyContent: 'center' }, initial: { ...tc.type.h2, color: tc.color.white }, identityCopy: { flex: 1 }, email: { ...tc.type.label, fontSize: 15, color: tc.color.ink }, fieldRow: { flexDirection: 'row', gap: tc.space.xs }, field: { flex: 1 }, chips: { flexDirection: 'row', flexWrap: 'wrap', gap: tc.space.xs, marginTop: tc.space.sm }, privacy: { marginTop: tc.space.lg, flexDirection: 'row', gap: tc.space.sm, alignItems: 'flex-start' }, privacyText: { color: tc.color.mint, flex: 1 }, save: { marginTop: tc.space.xl }, message: { ...tc.type.bodySmall, color: tc.color.danger, textAlign: 'center', marginTop: tc.space.sm }, success: { color: tc.color.mint } });
