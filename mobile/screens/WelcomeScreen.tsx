import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../auth/AuthContext';
import { Body, PrimaryButton, Screen } from '../components/ui';
import { tc } from '../design/tokens';

const orbit = [
  { icon: 'shopping-cart', label: 'Grocery' },
  { icon: 'shopping-bag', label: 'Shopping' },
  { icon: 'navigation', label: 'Mobility' },
  { icon: 'send', label: 'Flights' },
] as const;

export default function WelcomeScreen({ navigation }: any) {
  const { continueAsGuest } = useAuth();
  return <Screen contentStyle={styles.content}>
    <View style={styles.brand}><LinearGradient colors={[tc.color.iris, tc.color.irisBright]} style={styles.mark}><Text style={styles.markText}>TC</Text></LinearGradient><Text style={styles.brandName}>TrueCost</Text></View>
    <View style={styles.trust}><Feather name="shield" size={13} color={tc.color.iris} /><Text style={styles.trustText}>Evidence-aware comparisons</Text></View>

    <Text accessibilityRole="header" style={styles.title}>Compare smarter.{`\n`}Choose with clarity.</Text>
    <Body muted style={styles.lede}>Compare observed prices, delivery details and available options across categories, in one calm decision flow.</Body>

    <View style={styles.visual}>
      <View style={styles.glow} />
      <View style={styles.platform} />
      {orbit.map((item, index) => <View key={item.label} style={[styles.orbitCard, index === 0 && styles.o1, index === 1 && styles.o2, index === 2 && styles.o3, index === 3 && styles.o4]}><View style={styles.orbitIcon}><Feather name={item.icon} size={19} color={tc.color.iris} /></View><Text style={styles.orbitText}>{item.label}</Text></View>)}
      <LinearGradient colors={[tc.color.iris, tc.color.irisBright]} style={styles.best}><Feather name="zap" size={21} color={tc.color.white} /><Text style={styles.bestText}>TrueCost</Text><Text style={styles.bestSub}>Compare</Text></LinearGradient>
    </View>

    <View style={styles.benefits}>
      <Benefit icon="search" title="All-in-one" body="Start with your need" />
      <Benefit icon="shield" title="Evidence first" body="See freshness" />
      <Benefit icon="zap" title="Fast to act" body="Open provider" />
    </View>

    <PrimaryButton label="Get started" icon="arrow-right" onPress={() => navigation.navigate('PhoneAuth')} style={styles.primary} />
    <Pressable accessibilityRole="button" onPress={() => navigation.navigate('Auth')} style={({ pressed }) => [styles.email, pressed && styles.pressed]}><Feather name="mail" size={15} color={tc.color.iris} /><Text style={styles.emailText}>Use email instead</Text></Pressable>
    <Pressable accessibilityRole="button" onPress={() => void continueAsGuest()} style={({ pressed }) => [styles.guest, pressed && styles.pressed]}><Text style={styles.guestText}>Continue as guest</Text></Pressable>
    <Text style={styles.legal}>By continuing, you agree to the product terms and privacy policy.</Text>
  </Screen>;
}

function Benefit({ icon, title, body }: { icon: React.ComponentProps<typeof Feather>['name']; title: string; body: string }) {
  return <View style={styles.benefit}><View style={styles.benefitIcon}><Feather name={icon} size={16} color={tc.color.iris} /></View><Text style={styles.benefitTitle}>{title}</Text><Text style={styles.benefitBody}>{body}</Text></View>;
}

const styles = StyleSheet.create({
  content: { paddingTop: 18, paddingBottom: 28, justifyContent: 'center' }, pressed: { opacity: 0.68 },
  brand: { alignSelf: 'center', flexDirection: 'row', alignItems: 'center', gap: 9 }, mark: { width: 35, height: 35, borderRadius: 11, alignItems: 'center', justifyContent: 'center', transform: [{ rotate: '-4deg' }] }, markText: { color: tc.color.white, fontSize: 11, fontWeight: '900', letterSpacing: -0.6 }, brandName: { color: tc.color.ink, fontSize: 21, fontWeight: '800', letterSpacing: -0.6 },
  trust: { alignSelf: 'center', flexDirection: 'row', alignItems: 'center', gap: 5, marginTop: 9, paddingHorizontal: 9, paddingVertical: 5, borderRadius: tc.radius.pill, backgroundColor: tc.color.irisSoft }, trustText: { color: tc.color.irisDark, fontSize: 9, fontWeight: '700' },
  title: { color: tc.color.ink, fontSize: 30, lineHeight: 35, fontWeight: '800', letterSpacing: -0.9, textAlign: 'center', marginTop: 22 }, lede: { maxWidth: 340, alignSelf: 'center', textAlign: 'center', marginTop: 10, fontSize: 13, lineHeight: 19 },
  visual: { height: 206, marginTop: 10, position: 'relative' }, glow: { position: 'absolute', width: 240, height: 116, borderRadius: 80, backgroundColor: '#EEE8FF', alignSelf: 'center', left: '50%', marginLeft: -120, top: 66, opacity: 0.8 }, platform: { position: 'absolute', width: 270, height: 58, borderRadius: 80, backgroundColor: '#E5DEFF', alignSelf: 'center', left: '50%', marginLeft: -135, bottom: 14, transform: [{ scaleY: 0.58 }] },
  orbitCard: { position: 'absolute', width: 70, height: 88, borderRadius: 15, borderWidth: 1, borderColor: '#E3DEFA', backgroundColor: 'rgba(255,255,255,0.96)', alignItems: 'center', justifyContent: 'center', ...tc.shadow.card }, o1: { left: '3%', top: 78, transform: [{ rotate: '-8deg' }] }, o2: { left: '24%', top: 55, transform: [{ rotate: '-3deg' }] }, o3: { right: '24%', top: 55, transform: [{ rotate: '3deg' }] }, o4: { right: '3%', top: 78, transform: [{ rotate: '8deg' }] }, orbitIcon: { width: 34, height: 34, borderRadius: 12, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, orbitText: { color: tc.color.inkSoft, fontSize: 9, fontWeight: '700', marginTop: 7 },
  best: { position: 'absolute', width: 82, height: 105, borderRadius: 18, alignSelf: 'center', left: '50%', marginLeft: -41, top: 38, alignItems: 'center', justifyContent: 'center', zIndex: 5, borderWidth: 3, borderColor: tc.color.white, ...tc.shadow.rail }, bestText: { color: tc.color.white, fontSize: 12, fontWeight: '900', marginTop: 6 }, bestSub: { color: 'rgba(255,255,255,0.78)', fontSize: 9, marginTop: 2 },
  benefits: { flexDirection: 'row', gap: 8 }, benefit: { flex: 1, minHeight: 78, alignItems: 'center', padding: 8, borderRadius: 14, borderWidth: 1, borderColor: tc.color.line, backgroundColor: tc.color.surface }, benefitIcon: { width: 30, height: 30, borderRadius: 10, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, benefitTitle: { color: tc.color.ink, fontSize: 10, fontWeight: '800', marginTop: 5 }, benefitBody: { color: tc.color.muted, fontSize: 8, marginTop: 1, textAlign: 'center' },
  primary: { marginTop: 16 }, email: { minHeight: 46, borderRadius: tc.radius.sm, borderWidth: 1, borderColor: tc.color.line, backgroundColor: tc.color.surface, marginTop: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 }, emailText: { color: tc.color.iris, fontSize: 12, fontWeight: '800' }, guest: { minHeight: 40, alignItems: 'center', justifyContent: 'center' }, guestText: { color: tc.color.inkSoft, fontSize: 11, fontWeight: '700' }, legal: { color: tc.color.muted, fontSize: 8, lineHeight: 12, textAlign: 'center', marginTop: 5 },
});
