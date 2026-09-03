import React, { useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useAuth } from '../auth/AuthContext';
import { ApiError } from '../api/client';
import { AppHeader, Body, Field, PrimaryButton, Screen, Title } from '../components/ui';
import { tc } from '../design/tokens';

export default function AuthScreen({ navigation }: any) {
  const { signIn } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const emailError = useMemo(() => email && !/^\S+@\S+\.\S+$/.test(email) ? 'Enter a valid email address.' : '', [email]);
  const passwordError = useMemo(() => password && password.length < 8 ? 'Use at least 8 characters.' : '', [password]);
  const submit = async () => {
    if (!email || !password || emailError || passwordError) { setError('Complete both fields to continue.'); return; }
    setBusy(true); setError('');
    try { await signIn(email, password, mode === 'register'); }
    catch (cause) { setError(cause instanceof ApiError ? cause.message : 'Unable to continue. Try again.'); }
    finally { setBusy(false); }
  };
  return <Screen contentStyle={styles.content}>
    <AppHeader subtitle="Your account, securely restored." onBack={() => navigation.goBack()} />
    <Text style={styles.kicker}>{mode === 'register' ? 'CREATE YOUR TRUECOST ID' : 'WELCOME BACK'}</Text>
    <Title size="display">{mode === 'register' ? 'Keep your best decisions.' : 'Your savings, ready.'}</Title>
    <Body muted style={styles.lede}>{mode === 'register' ? 'Create an account to save comparisons, carts and price watches.' : 'Sign in to continue from your saved carts and comparisons.'}</Body>
    <View style={styles.form}>
      <Field label="Email address" icon="mail" value={email} onChangeText={setEmail} autoCapitalize="none" autoCorrect={false} autoComplete="email" textContentType="emailAddress" keyboardType="email-address" returnKeyType="next" error={emailError} />
      <View>
        <Field label="Password" icon="lock" value={password} onChangeText={setPassword} secureTextEntry={!showPassword} autoComplete={mode === 'register' ? 'new-password' : 'current-password'} textContentType={mode === 'register' ? 'newPassword' : 'password'} returnKeyType="done" onSubmitEditing={() => void submit()} error={passwordError} />
        <Pressable accessibilityRole="button" accessibilityLabel={showPassword ? 'Hide password' : 'Show password'} hitSlop={10} style={styles.eye} onPress={() => setShowPassword(value => !value)}><Feather name={showPassword ? 'eye-off' : 'eye'} size={19} color={tc.color.muted} /></Pressable>
      </View>
      {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
      <PrimaryButton label={mode === 'register' ? 'Create account' : 'Sign in'} icon="arrow-right" loading={busy} onPress={() => void submit()} />
      <PrimaryButton label="Continue with mobile number" icon="smartphone" variant="outline" disabled={busy} onPress={() => navigation.navigate('PhoneAuth')} />
    </View>
    <Pressable accessibilityRole="button" style={styles.switcher} onPress={() => { setMode(value => value === 'login' ? 'register' : 'login'); setError(''); }}>
      <Text style={styles.switchText}>{mode === 'register' ? 'Already have an account? ' : 'New to TrueCost? '}<Text style={styles.switchStrong}>{mode === 'register' ? 'Sign in' : 'Create one'}</Text></Text>
    </Pressable>
    <Body muted style={styles.legal}>By continuing, you agree to the product terms and privacy policy. Passwords are never stored on this device.</Body>
  </Screen>;
}
const styles = StyleSheet.create({
  content: { paddingTop: tc.space.sm }, kicker: { ...tc.type.eyebrow, color: tc.color.iris, marginTop: 30, marginBottom: tc.space.sm },
  lede: { marginTop: tc.space.md, fontSize: 16 }, form: { gap: tc.space.md, marginTop: tc.space.xl },
  eye: { position: 'absolute', right: 6, bottom: 3, width: 48, height: 48, alignItems: 'center', justifyContent: 'center' },
  error: { ...tc.type.bodySmall, color: tc.color.danger }, switcher: { minHeight: 48, alignItems: 'center', justifyContent: 'center', marginTop: tc.space.md },
  switchText: { ...tc.type.bodySmall, color: tc.color.muted }, switchStrong: { color: tc.color.iris, fontWeight: '800' },
  legal: { marginTop: tc.space.xl, textAlign: 'center', fontSize: 12 },
});
