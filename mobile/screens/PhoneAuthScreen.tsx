import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { ApiError, publicApi } from '../api/client';
import { AppHeader, Body, Card, Field, PrimaryButton, Screen, Title } from '../components/ui';
import { tc } from '../design/tokens';

type OtpRequestResponse = { challenge_id: string; expires_in_seconds: number; resend_after_seconds: number; delivery_channel: 'sms' | 'development_console' };

export default function PhoneAuthScreen({ navigation }: any) {
  const [phone, setPhone] = useState('+91');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const normalized = phone.replace(/[\s()-]/g, '');

  const submit = async () => {
    if (!/^\+[1-9]\d{7,14}$/.test(normalized)) {
      setError('Enter a complete international mobile number.');
      return;
    }
    setBusy(true); setError('');
    try {
      const response = await publicApi<OtpRequestResponse>('/auth/request-otp', { method: 'POST', body: JSON.stringify({ phone_number: normalized }) });
      navigation.navigate('OtpVerification', { phoneNumber: normalized, ...response });
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : 'We could not send the verification code.');
    } finally { setBusy(false); }
  };

  return <Screen contentStyle={styles.content} keyboardShouldPersistTaps="handled">
    <AppHeader subtitle="Find true value. Every time." onBack={() => navigation.goBack()} />
    <Text style={styles.kicker}>MOBILE SIGN IN</Text>
    <Title size="display" style={styles.title}>Welcome back</Title>
    <Body muted style={styles.lede}>Compare across categories, then keep your carts, alerts and decisions together.</Body>
    <Card tone="iris" style={styles.preview}>
      <View style={styles.previewIcons}>{(['shopping-cart', 'shopping-bag', 'send', 'navigation', 'home'] as const).map(icon => <View key={icon} style={styles.previewIcon}><Feather name={icon} size={17} color={tc.color.iris} /></View>)}</View>
      <Body muted style={styles.previewCopy}>One account for grocery, shopping, travel, mobility and stays.</Body>
    </Card>
    <View style={styles.form}>
      <Field label="Mobile number" icon="smartphone" value={phone} onChangeText={value => { setPhone(value); setError(''); }} keyboardType="phone-pad" autoComplete="tel" textContentType="telephoneNumber" returnKeyType="done" onSubmitEditing={() => void submit()} />
      {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
      <PrimaryButton label="Continue with OTP" icon="arrow-right" loading={busy} onPress={() => void submit()} />
    </View>
    <Body muted style={styles.safe}>We send a six-digit sign-in code. TrueCost never asks for a bank or payment OTP.</Body>
  </Screen>;
}

const styles = StyleSheet.create({
  content: { paddingTop: tc.space.sm }, kicker: { ...tc.type.eyebrow, color: tc.color.iris, marginTop: 30, textAlign: 'center' }, title: { marginTop: 8, textAlign: 'center' }, lede: { marginTop: 8, fontSize: 14, textAlign: 'center' },
  preview: { marginTop: 22, alignItems: 'center' }, previewIcons: { flexDirection: 'row', gap: 8 }, previewIcon: { width: 38, height: 38, borderRadius: 13, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' }, previewCopy: { textAlign: 'center', marginTop: 8, fontSize: 11 },
  form: { gap: tc.space.md, marginTop: 22 }, error: { ...tc.type.bodySmall, color: tc.color.danger }, safe: { marginTop: tc.space.xl, textAlign: 'center', fontSize: 11 },
});
