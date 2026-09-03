import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { tc } from '../../design/tokens';

interface State { hasError: boolean; }
interface Props { children: React.ReactNode; fallbackMessage?: string; onReset?: () => void; }

export default class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false };
  static getDerivedStateFromError(): State { return { hasError: true }; }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    if (__DEV__) console.error('[TrueCost ErrorBoundary]', error.message, info.componentStack);
  }
  reset = () => { this.setState({ hasError: false }); this.props.onReset?.(); };
  render() {
    if (!this.state.hasError) return this.props.children;
    return <View accessibilityRole="alert" style={styles.page}><View style={styles.icon}><Feather name="alert-triangle" size={27} color={tc.color.danger} /></View><Text style={styles.title}>TrueCost needs a fresh start</Text><Text style={styles.body}>{this.props.fallbackMessage || 'An interface component stopped unexpectedly. Your account data was not changed.'}</Text><Pressable accessibilityRole="button" onPress={this.reset} style={({ pressed }) => [styles.button, pressed && styles.pressed]}><Text style={styles.buttonText}>Try again</Text></Pressable></View>;
  }
}
const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: tc.color.bg, alignItems: 'center', justifyContent: 'center', padding: tc.space.xl },
  icon: { width: 60, height: 60, borderRadius: 20, backgroundColor: tc.color.dangerSoft, alignItems: 'center', justifyContent: 'center' },
  title: { ...tc.type.h2, color: tc.color.ink, textAlign: 'center', marginTop: tc.space.lg }, body: { ...tc.type.bodySmall, color: tc.color.muted, textAlign: 'center', marginTop: tc.space.sm },
  button: { minWidth: 150, minHeight: 52, borderRadius: tc.radius.md, backgroundColor: tc.color.iris, alignItems: 'center', justifyContent: 'center', marginTop: tc.space.lg }, buttonText: { ...tc.type.label, color: tc.color.white, fontSize: 15 }, pressed: { opacity: 0.75 },
});
