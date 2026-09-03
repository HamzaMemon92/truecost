import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Body, Card, Eyebrow, IconButton, Screen, SectionHeader, Title } from '../components/ui';
import { tc } from '../design/tokens';

const issues = [
  { category: 'wrong_price', icon: 'dollar-sign' as const, title: 'Wrong price', body: 'Report a mismatch between an observation and provider checkout.' },
  { category: 'wrong_product', icon: 'package' as const, title: 'Wrong product', body: 'Tell us when a result appears to match a different item.' },
  { category: 'broken_link', icon: 'link-2' as const, title: 'Broken provider link', body: 'Report a supplied destination that no longer opens.' },
  { category: 'refund_help', icon: 'rotate-ccw' as const, title: 'Refund help', body: 'Understand which provider owns an order or refund.' },
  { category: 'other', icon: 'message-circle' as const, title: 'Something else', body: 'Send a detailed product or experience report.' },
];
const faqs = [
  ['Does TrueCost guarantee the checkout price?', 'No. We show the latest supplied observation and its freshness. The provider confirms final price, availability, taxes and eligibility.'],
  ['How is the best option selected?', 'Authoritative totals and rankings come from deterministic backend logic. Explanations describe that result; they do not recalculate it.'],
  ['Does scanning identify every product?', 'No. Scan results retain provenance and remain unverified until a user confirms the product or a configured recognition source supplies evidence.'],
  ['Who handles my purchase or refund?', 'Your purchase is completed with the selected provider. That provider owns payment, fulfilment, cancellation and refund support.'],
];

export default function HelpSupportScreen({ navigation }: any) {
  const [open, setOpen] = useState<number | null>(null);
  return <Screen><IconButton icon="arrow-left" label="Back" onPress={() => navigation.goBack()} /><Eyebrow style={styles.eyebrow}>HELP, SUPPORT & TRUST</Eyebrow><Title size="display">Clear answers when a decision feels wrong.</Title><Body muted style={styles.intro}>Reports are attached only to the context you choose to submit. Never include passwords, OTPs, or full payment details.</Body>
    <SectionHeader title="Report an issue" /><View style={styles.list}>{issues.map(item => <Pressable key={item.category} accessibilityRole="button" accessibilityLabel={item.title} onPress={() => navigation.navigate('ReportIssue', { category: item.category, title: item.title })} style={({ pressed }) => [pressed && styles.pressed]}><Card style={styles.issue}><View style={styles.icon}><Feather name={item.icon} size={20} color={tc.color.iris} /></View><View style={styles.copy}><Text style={styles.title}>{item.title}</Text><Body muted>{item.body}</Body></View><Feather name="chevron-right" size={20} color={tc.color.muted} /></Card></Pressable>)}</View>
    <SectionHeader title="Trust & verification" /><Card tone="mint" style={styles.trust}><TrustRow icon="eye" title="Observed facts stay labeled" body="Price, time and availability are shown only when supplied by a source." /><TrustRow icon="cpu" title="Math stays deterministic" body="The backend calculates totals and rankings; explanatory copy cannot override them." /><TrustRow icon="external-link" title="Handoff stays explicit" body="Before leaving TrueCost you can review provider, expected total, freshness and destination." /></Card>
    <SectionHeader title="Frequently asked questions" /><View style={styles.list}>{faqs.map(([question, answer], index) => <Pressable key={question} accessibilityRole="button" accessibilityState={{ expanded: open === index }} onPress={() => setOpen(open === index ? null : index)}><Card style={styles.faq}><View style={styles.faqHead}><Text style={styles.faqTitle}>{question}</Text><Feather name={open === index ? 'minus' : 'plus'} size={18} color={tc.color.iris} /></View>{open === index ? <Body muted style={styles.answer}>{answer}</Body> : null}</Card></Pressable>)}</View>
  </Screen>;
}
function TrustRow({ icon, title, body }: { icon: React.ComponentProps<typeof Feather>['name']; title: string; body: string }) { return <View style={styles.trustRow}><View style={styles.trustIcon}><Feather name={icon} size={18} color={tc.color.mint} /></View><View style={styles.copy}><Text style={styles.title}>{title}</Text><Body muted>{body}</Body></View></View>; }
const styles = StyleSheet.create({ eyebrow: { marginTop: tc.space.lg, marginBottom: tc.space.xs }, intro: { marginTop: tc.space.sm }, list: { gap: tc.space.xs }, issue: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, icon: { width: 46, height: 46, borderRadius: 16, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, copy: { flex: 1 }, title: { ...tc.type.label, color: tc.color.ink, marginBottom: 2 }, trust: { gap: tc.space.md }, trustRow: { flexDirection: 'row', gap: tc.space.sm }, trustIcon: { width: 40, height: 40, borderRadius: 14, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' }, faq: { padding: tc.space.md }, faqHead: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, faqTitle: { ...tc.type.label, color: tc.color.ink, flex: 1 }, answer: { marginTop: tc.space.sm }, pressed: { opacity: .72 } });
