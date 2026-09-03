import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import {
  AppHeader,
  Body,
  Divider,
  EmptyState,
  Eyebrow,
  PrimaryButton,
  ProviderLogo,
  Screen,
  SectionHeader,
  WinnerCard,
} from '../components/ui';
import { SystemState } from '../components/SystemState';
import { formatCurrency, TC, tc } from '../design/tokens';

export default function ComparisonScreen({ route, navigation }: any) {
  const options: any[] = Array.isArray(route.params?.options) ? route.params.options : [];
  const winnerId = route.params?.decision?.winner_id || route.params?.decision?.provider || null;

  const winnerOption = options.find(o =>
    o.isBest === true || winnerId === o.id || winnerId === (o.provider || o.name)
  ) ?? (options.length === 1 ? options[0] : null);

  const otherOptions = options.filter(o => o !== winnerOption);

  return (
    <Screen>
      <AppHeader
        subtitle="Universal comparison"
        onBack={() => navigation.goBack()}
      />

      {/* Page heading */}
      <Eyebrow style={styles.eyebrow}>COMPARISON</Eyebrow>
      <Text style={styles.pageTitle}>
        {route.params?.title || 'Your available options'}
      </Text>
      <Body muted style={styles.lede}>
        Rows show only confirmed observations. Missing fees remain explicitly unknown — never assumed as zero.
      </Body>

      {route.params?.partial ? <SystemState kind="partial" compact /> : null}

      {!options.length ? (
        <EmptyState
          icon="search"
          title="No options to compare"
          body="No observations were recorded for this query. Try adjusting your search."
          actionLabel="Back to search"
          onAction={() => navigation.goBack()}
        />
      ) : (
        <>
          {/* Winner card — most important moment */}
          {winnerOption && (
            <>
              <SectionHeader title="TrueCost recommendation" style={styles.sectionGap} />
              <WinnerCard
                provider={winnerOption.provider || winnerOption.name || 'Best Option'}
                productName={route.params?.title || winnerOption.name || 'Selected option'}
                price={winnerOption.total ?? winnerOption.true_cost ?? winnerOption.price ?? 0}
                savings={
                  otherOptions.length > 0
                    ? Math.max(...otherOptions.map(o => o.total ?? o.true_cost ?? o.price ?? 0)) -
                      (winnerOption.total ?? winnerOption.true_cost ?? winnerOption.price ?? 0)
                    : undefined
                }
                reason={route.params?.decision?.reason}
                providerCount={{ compared: options.length, total: options.length }}
                onPress={() => navigation.navigate('CheckoutHandoff', {
                  product: route.params?.product,
                  offer: winnerOption,
                  reason: winnerOption.reason || route.params?.decision?.reason,
                  notRecommended: false,
                })}
              />
            </>
          )}

          {/* Other options */}
          {otherOptions.length > 0 && (
            <>
              <SectionHeader
                title={`All ${options.length} options`}
                style={styles.sectionGap}
              />
              <View style={styles.optionList}>
                {options.map((option, index) => {
                  const provider = option.provider || option.name || `Option ${index + 1}`;
                  const isWinner = option.isBest === true || winnerId === option.id || winnerId === provider;
                  const price = option.total ?? option.true_cost ?? option.price;

                  return (
                    <OptionCard
                      key={`${option.id ?? provider}:${index}`}
                      provider={provider}
                      price={price}
                      currency={option.currency}
                      delivery={option.delivery || option.delivery_time}
                      availability={option.availability}
                      fees={option.fees ?? option.estimated_fees}
                      missingCount={option.missing_items?.length ?? 0}
                      isWinner={isWinner}
                      hasDecision={!!winnerId}
                      onPress={() => navigation.navigate('CheckoutHandoff', {
                        product: route.params?.product,
                        offer: option,
                        reason: option.reason || route.params?.decision?.reason,
                        notRecommended: !isWinner && !!winnerId,
                      })}
                    />
                  );
                })}
              </View>
            </>
          )}

          {/* Why this option won */}
          {route.params?.decision && (
            <PrimaryButton
              label="Why this option won"
              variant="outline"
              icon="info"
              onPress={() => navigation.navigate('DecisionExplanation', {
                decision: route.params.decision,
                options,
              })}
              style={styles.explainBtn}
            />
          )}
        </>
      )}
    </Screen>
  );
}

// ─── Option Card ────────────────────────────────────────────────────────────────
function OptionCard({
  provider, price, currency, delivery, availability, fees,
  missingCount, isWinner, hasDecision, onPress,
}: {
  provider: string;
  price?: number | null;
  currency?: string;
  delivery?: string | null;
  availability?: string | null;
  fees?: number | null;
  missingCount: number;
  isWinner: boolean;
  hasDecision: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.optionCard,
        isWinner && styles.optionCardWinner,
        pressed && styles.pressed,
      ]}
    >
      {isWinner && (
        <LinearGradient
          colors={['#E4F9F4', '#FAFAF8']}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        />
      )}

      {/* Provider row */}
      <View style={styles.optionHeader}>
        <ProviderLogo provider={provider} size="sm" />
        <View style={styles.flex}>
          <Text style={styles.providerName}>{provider}</Text>
          {isWinner ? (
            <Text style={styles.winnerLabel}>RECOMMENDATION</Text>
          ) : hasDecision ? (
            <Text style={styles.altLabel}>ALTERNATIVE</Text>
          ) : null}
        </View>
        <View style={styles.priceGroup}>
          {price != null ? (
            <Text style={[styles.price, isWinner && styles.priceWinner]}>
              {formatCurrency(price, currency || 'INR')}
            </Text>
          ) : (
            <Text style={styles.priceUnknown}>—</Text>
          )}
        </View>
      </View>

      {/* Facts row */}
      <View style={styles.factsRow}>
        <Fact label="Delivery" value={delivery} />
        <Fact label="Availability" value={availability} />
        <Fact label="Fees" value={fees} isCurrency={typeof fees === 'number'} />
      </View>

      {missingCount > 0 && (
        <View style={styles.missingRow}>
          <Feather name="alert-circle" size={12} color={TC.color.danger} />
          <Text style={styles.missingText}>{missingCount} item(s) not found</Text>
        </View>
      )}

      {/* CTA */}
      <View style={styles.cta}>
        <Text style={styles.ctaText}>Review handoff</Text>
        <Feather name="arrow-right" size={14} color={TC.color.iris} />
      </View>
    </Pressable>
  );
}

// ─── Fact Chip ─────────────────────────────────────────────────────────────────
function Fact({ label, value, isCurrency }: { label: string; value: unknown; isCurrency?: boolean }) {
  const display = value === null || value === undefined || value === ''
    ? 'Not supplied'
    : isCurrency
    ? formatCurrency(Number(value))
    : String(value);
  const isUnknown = display === 'Not supplied';
  return (
    <View style={styles.fact}>
      <Text style={styles.factLabel}>{label}</Text>
      <Text numberOfLines={2} style={[styles.factValue, isUnknown && styles.factUnknown]}>
        {display}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  pressed: { opacity: 0.72 },

  eyebrow: { marginTop: TC.space.md, marginBottom: TC.space.xs },
  pageTitle: { ...TC.type.h1, color: TC.color.ink, marginBottom: TC.space.sm },
  lede: { lineHeight: 20, marginBottom: TC.space.base },

  sectionGap: { marginTop: TC.space.xl },
  optionList: { gap: TC.space.sm },

  // Option card
  optionCard: {
    backgroundColor: TC.color.surfaceCard,
    borderRadius: TC.radius.card,
    borderWidth: 1,
    borderColor: TC.color.line,
    overflow: 'hidden',
    ...TC.shadow.xs,
  },
  optionCardWinner: {
    borderColor: TC.color.mint,
    borderWidth: 1.5,
    ...TC.shadow.winner,
  },

  optionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: TC.space.md,
    padding: TC.space.base,
    paddingBottom: TC.space.sm,
  },
  providerName: { ...TC.type.h3, color: TC.color.ink },
  winnerLabel: { ...TC.type.micro, color: TC.color.mintDeep, letterSpacing: 0.8, marginTop: 2 },
  altLabel: { ...TC.type.micro, color: TC.color.muted, letterSpacing: 0.8, marginTop: 2 },
  priceGroup: { alignItems: 'flex-end' },
  price: { ...TC.type.priceMain, color: TC.color.ink },
  priceWinner: { color: TC.color.mintDeep },
  priceUnknown: { ...TC.type.priceMain, color: TC.color.muted },

  // Facts row
  factsRow: {
    flexDirection: 'row',
    gap: TC.space.sm,
    paddingHorizontal: TC.space.base,
    paddingBottom: TC.space.sm,
  },
  fact: {
    flex: 1,
    backgroundColor: TC.color.surfaceAlt,
    borderRadius: TC.radius.sm,
    padding: TC.space.sm,
    minHeight: 52,
  },
  factLabel: { ...TC.type.caption, color: TC.color.muted, fontSize: 10 },
  factValue: { ...TC.type.label, color: TC.color.ink, fontSize: 11, marginTop: 2 },
  factUnknown: { color: TC.color.muted, fontStyle: 'italic' },

  missingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: TC.space.xs,
    paddingHorizontal: TC.space.base,
    paddingBottom: TC.space.sm,
  },
  missingText: { ...TC.type.caption, color: TC.color.danger },

  cta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: TC.space.xs,
    paddingHorizontal: TC.space.base,
    paddingVertical: TC.space.md,
    borderTopWidth: 1,
    borderTopColor: TC.color.line,
  },
  ctaText: { ...TC.type.label, color: TC.color.iris },

  explainBtn: { marginTop: TC.space.xl },
});
