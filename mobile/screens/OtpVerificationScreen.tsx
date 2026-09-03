import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useAuth } from '../auth/AuthContext';
import { ApiError, publicApi, SessionTokens } from '../api/client';
import { AppHeader, Body, Card, Field, PrimaryButton, Screen, Title } from '../components/ui';
import { tc } from '../design/tokens';

type OtpResponse = { challenge_id: string; expires_in_seconds: number; resend_after_seconds: number; delivery_channel: 'sms' | 'development_console' };

export default function OtpVerificationScreen({ navigation, route }: any) {
  const { updateSession } = useAuth();
  const [challengeId, setChallengeId] = useState(route.params.challenge_id as string);
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [seconds, setSeconds] = useState(route.params.resend_after_seconds as number);
  const [deliveryChannel, setDeliveryChannel] = useState<OtpResponse['delivery_channel']>(route.params.delivery_channel || 'sms');
  const phoneNumber = route.params.phoneNumber as string;
  useEffect(() => { if (seconds <= 0) return; const timer = setInterval(() => setSeconds(value => Math.max(0, value - 1)), 1000); return () => clearInterval(timer); }, [seconds > 0]);

  const verify = async () => {
    if (!/^\d{6}$/.test(code)) { setError('Enter the complete six-digit code.'); return; }
    setBusy(true); setError('');
    try {
      const tokens = await publicApi<SessionTokens>('/auth/verify-otp', { method: 'POST', body: JSON.stringify({ challenge_id: challengeId, code }) });
      await updateSession(tokens);
    } catch (cause) { setError(cause instanceof ApiError ? cause.message : 'The code could not be verified.'); }
    finally { setBusy(false); }
  };

  const resend = async () => {
    if (seconds > 0) return;
    setBusy(true); setError(''); setCode('');
    try {
      const response = await publicApi<OtpResponse>('/auth/request-otp', { method: 'POST', body: JSON.stringify({ phone_number: phoneNumber }) });
      setChallengeId(response.challenge_id); setSeconds(response.resend_after_seconds); setDeliveryChannel(response.delivery_channel);
    } catch (cause) { setError(cause instanceof ApiError ? cause.message : 'A new code could not be sent.'); }
    finally { setBusy(false); }
  };

  return <Screen contentStyle={styles.content} keyboardShouldPersistTaps="handled">
    <AppHeader subtitle="Secure mobile sign in" onBack={() => navigation.goBack()} />
    <Text style={styles.kicker}>VERIFY YOUR NUMBER</Text>
    <Title size="display" style={styles.title}>Check your messages</Title>
    <Body muted style={styles.lede}>Enter the code sent to {phoneNumber.replace(/.(?=.{4})/g, '\u2022')}.</Body>
    {deliveryChannel === 'development_console' ? <Card tone="amber" style={styles.developmentNotice}><Text style={styles.developmentTitle}>Development SMS mode</Text><Body muted>The code is printed in the FastAPI backend terminal. Configure Twilio credentials to deliver it to this phone.</Body></Card> : null}
    <View style={styles.codePreview}>{Array.from({ length: 6 }, (_, index) => <View key={index} style={[styles.codeBox, code[index] && styles.codeBoxFilled]}><Text style={styles.codeDigit}>{code[index] || ''}</Text></View>)}</View>
    <View style={styles.form}>
      <Field label="Six-digit code" icon="shield" value={code} onChangeText={value => { setCode(value.replace(/\D/g, '').slice(0, 6)); setError(''); }} keyboardType="number-pad" autoComplete="sms-otp" textContentType="oneTimeCode" returnKeyType="done" onSubmitEditing={() => void verify()} />
      <Text accessibilityLiveRegion="polite" style={styles.timer}>{seconds > 0 ? `Send another code in ${seconds}s` : 'You can request a new code now.'}</Text>
      {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
      <PrimaryButton label="Verify and continue" icon="check" loading={busy} onPress={() => void verify()} />
      <PrimaryButton label="Send a new code" variant="outline" disabled={seconds > 0 || busy} onPress={() => void resend()} />
    </View>
  </Screen>;
}

const styles = StyleSheet.create({
  content: { paddingTop: tc.space.sm }, kicker: { ...tc.type.eyebrow, color: tc.color.iris, marginTop: 34, textAlign: 'center' }, title: { marginTop: 8, textAlign: 'center' }, lede: { marginTop: 8, fontSize: 14, textAlign: 'center' },
  developmentNotice: { marginTop: 16, gap: 3 }, developmentTitle: { ...tc.type.label, color: tc.color.amber }, codePreview: { flexDirection: 'row', justifyContent: 'center', gap: 7, marginTop: 24 }, codeBox: { width: 42, height: 48, borderRadius: 12, borderWidth: 1, borderColor: tc.color.lineStrong, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' }, codeBoxFilled: { borderColor: tc.color.iris, backgroundColor: tc.color.irisSoft }, codeDigit: { color: tc.color.ink, fontSize: 19, fontWeight: '800', fontVariant: ['tabular-nums'] },
  form: { gap: tc.space.md, marginTop: 18 }, timer: { ...tc.type.bodySmall, color: tc.color.muted, textAlign: 'center' }, error: { ...tc.type.bodySmall, color: tc.color.danger },
});
