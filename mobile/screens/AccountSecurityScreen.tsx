import React, { useState } from 'react';
import { Pressable, Share, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { api, publicApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { Body, Card, Eyebrow, Field, IconButton, PrimaryButton, Screen, SectionHeader, Title } from '../components/ui';
import { SystemState } from '../components/SystemState';
import { tc } from '../design/tokens';
import { useApiQuery } from '../query/useApiQuery';

type Session = { id: string; created_at: string; expires_at: string; revoked_at: string | null };
type Profile = { email: string | null; phone_number: string | null };

export default function AccountSecurityScreen({ navigation }: any) {
  const { session, updateSession, signOut } = useAuth();
  const sessions = useApiQuery<Session[]>('account-sessions', '/auth/sessions', { enabled: !!session, maxAge: 0 });
  const profile = useApiQuery<Profile>('security-profile', '/profiles/me', { enabled: !!session, maxAge: 30_000 });
  const [password, setPassword] = useState('');
  const [challengeId, setChallengeId] = useState('');
  const [otp, setOtp] = useState('');
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const isPhoneAccount = !!profile.data?.phone_number && !profile.data?.email;

  const revoke = async (id: string) => {
    if (!session) return;
    setBusy(id);
    try { await api(session, updateSession, `/auth/sessions/${id}`, { method: 'DELETE' }); await sessions.refetch(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not revoke the session.'); }
    finally { setBusy(''); }
  };
  const revokeAll = async () => {
    if (!session) return;
    setBusy('all');
    try { await api(session, updateSession, '/auth/sessions/revoke-all', { method: 'POST' }); await signOut(); }
    finally { setBusy(''); }
  };
  const exportAccount = async () => {
    if (!session) return;
    setBusy('export');
    try {
      const data = await api<Record<string, unknown>>(session, updateSession, '/profiles/me/export');
      await Share.share({ title: 'TrueCost account export', message: JSON.stringify(data, null, 2) });
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not create your export.'); }
    finally { setBusy(''); }
  };
  const requestReauthenticationCode = async () => {
    if (!profile.data?.phone_number) return;
    setBusy('otp'); setError('');
    try {
      const response = await publicApi<{ challenge_id: string }>('/auth/request-otp', { method: 'POST', body: JSON.stringify({ phone_number: profile.data.phone_number }) });
      setChallengeId(response.challenge_id);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not send a verification code.'); }
    finally { setBusy(''); }
  };
  const deleteAccount = async () => {
    if (!session) return;
    setBusy('delete'); setError('');
    try {
      let body: { password?: string; reauthentication_token?: string } = { password };
      if (isPhoneAccount) {
        const verified = await api<{ reauthentication_token: string }>(session, updateSession, '/auth/reauth/verify-otp', { method: 'POST', body: JSON.stringify({ challenge_id: challengeId, code: otp }) });
        body = { reauthentication_token: verified.reauthentication_token };
      }
      await api(session, updateSession, '/profiles/me', { method: 'DELETE', body: JSON.stringify(body) });
      await signOut();
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not delete your account.'); }
    finally { setBusy(''); }
  };

  return <Screen>
    <IconButton icon="arrow-left" label="Back" onPress={() => navigation.goBack()} />
    <Eyebrow style={styles.eyebrow}>PRIVACY & SECURITY</Eyebrow><Title size="display">Your account stays under your control.</Title>
    <Body muted style={styles.intro}>Export your data, revoke sessions, or permanently remove the account. Full payment credentials are never part of the profile.</Body>
    <SectionHeader title="Signed-in sessions" />
    {sessions.loading && !sessions.data ? <SystemState kind="loading" compact /> : sessions.error ? <SystemState kind="offline" compact actionLabel="Try again" onAction={() => void sessions.refetch()} /> : <View style={styles.sessions}>{sessions.data?.map((item, index) => <Card key={item.id} style={styles.session}><View style={styles.sessionIcon}><Feather name="smartphone" size={18} color={tc.color.iris} /></View><View style={styles.copy}><Text style={styles.title}>Session {index + 1}</Text><Body muted>Created {new Date(item.created_at).toLocaleString()}</Body><Text style={[styles.status, item.revoked_at && styles.revoked]}>{item.revoked_at ? 'Revoked' : `Active until ${new Date(item.expires_at).toLocaleDateString()}`}</Text></View>{!item.revoked_at ? <Pressable accessibilityRole="button" accessibilityLabel={`Revoke session ${index + 1}`} disabled={!!busy} onPress={() => void revoke(item.id)} style={styles.revoke}><Text style={styles.revokeText}>{busy === item.id ? 'Working…' : 'Revoke'}</Text></Pressable> : null}</Card>)}</View>}
    <PrimaryButton label="Sign out all sessions" variant="outline" icon="log-out" loading={busy === 'all'} onPress={() => void revokeAll()} style={styles.action} />
    <SectionHeader title="Your data" /><Card tone="mint"><Title size="h3">Portable account export</Title><Body muted style={styles.cardBody}>Creates a JSON snapshot of your profile and TrueCost-owned records for the system share sheet.</Body><PrimaryButton label="Create secure export" variant="mint" icon="download" loading={busy === 'export'} onPress={() => void exportAccount()} style={styles.cardAction} /></Card>
    <SectionHeader title="Danger zone" /><Card tone="danger"><Title size="h3">Delete account permanently</Title><Body muted style={styles.cardBody}>This removes your profile, saved decisions, carts, watches, activity, addresses and masked payment preferences. Provider revocation is queued before local metadata is removed.</Body>{confirming ? <>{isPhoneAccount ? <>{!challengeId ? <PrimaryButton label="Send verification code" variant="outline" icon="message-circle" loading={busy === 'otp'} onPress={() => void requestReauthenticationCode()} style={styles.cardAction} /> : <Field label="6-digit verification code" value={otp} onChangeText={setOtp} keyboardType="number-pad" maxLength={6} containerStyle={styles.password} />}</> : <Field label="Confirm your password" value={password} onChangeText={setPassword} secureTextEntry textContentType="password" containerStyle={styles.password} />}<PrimaryButton label="Permanently delete account" variant="danger" icon="trash-2" loading={busy === 'delete'} disabled={isPhoneAccount ? otp.length !== 6 : password.length < 8} onPress={() => void deleteAccount()} style={styles.cardAction} /></> : <PrimaryButton label="Review account deletion" variant="outline" icon="alert-triangle" onPress={() => setConfirming(true)} style={styles.cardAction} />}</Card>
    {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
  </Screen>;
}

const styles = StyleSheet.create({ eyebrow: { marginTop: tc.space.lg, marginBottom: tc.space.xs }, intro: { marginTop: tc.space.sm }, sessions: { gap: tc.space.xs }, session: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, sessionIcon: { width: 42, height: 42, borderRadius: 14, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, copy: { flex: 1 }, title: { ...tc.type.label, color: tc.color.ink }, status: { ...tc.type.eyebrow, color: tc.color.mint, marginTop: 3 }, revoked: { color: tc.color.muted }, revoke: { minWidth: 60, minHeight: 48, alignItems: 'center', justifyContent: 'center' }, revokeText: { ...tc.type.label, color: tc.color.danger }, action: { marginTop: tc.space.md }, cardBody: { marginTop: tc.space.xs }, cardAction: { marginTop: tc.space.md }, password: { marginTop: tc.space.md }, error: { ...tc.type.bodySmall, color: tc.color.danger, marginTop: tc.space.md } });
