import { createFileRoute } from "@tanstack/react-router";
import { ArrowUpRight, Leaf, PiggyBank, Receipt, Sparkles, TrendingDown } from "lucide-react";
import { AppShell } from "@/components/tc/app-shell";
import { BrandLogo } from "@/components/tc/brand-logo";
import {
  AnimatedNumber,
  KeyValue,
  Panel,
  PageHeader,
  PanelHeader,
  Stagger,
  StaggerItem,
  StatCard,
  Tag,
} from "@/components/tc/ui-kit";
import { TrendArea, TrendBars } from "@/components/tc/charts";
import { inr, monthlySavings, recentActivity, savingsByCategory, savingsTrend } from "@/lib/mock-data";

export const Route = createFileRoute("/savings")({
  head: () => ({
    meta: [
      { title: "Verified Savings — TrueCost" },
      {
        name: "description",
        content:
          "Track exactly how much money and time your agent has saved you over weeks, months and years.",
      },
      { property: "og:title", content: "Verified Savings — TrueCost" },
      {
        property: "og:description",
        content: "Audit your agent's performance and verify every dollar saved on TrueCost.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Savings,
});

function Savings() {
  return (
    <AppShell>
      <div className="space-y-5">
        <PageHeader
          eyebrow={<Tag tone="brand" icon={<Sparkles className="h-3 w-3" />}>Verified & attributed</Tag>}
          title="Your savings ledger"
          subtitle="Only counted when you accepted a comparison and we can prove the alternative price."
          actions={
            <span className="hidden items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-semibold text-muted-foreground sm:flex">
              <Receipt className="h-3.5 w-3.5 text-brand" /> 42 receipts
            </span>
          }
        />

        <Stagger className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StaggerItem>
            <StatCard
              label="Saved this month"
              value={<AnimatedNumber value={31240} format={(n) => inr(Math.round(n))} />}
              sub="42 accepted decisions"
              delta="+18.4%"
              icon={<PiggyBank className="h-4 w-4" />}
            />
          </StaggerItem>
          <StaggerItem>
            <StatCard
              label="Saved this year"
              value={<AnimatedNumber value={84900} format={(n) => inr(Math.round(n))} />}
              sub="Since January"
              delta="+₹12,860"
              icon={<TrendingDown className="h-4 w-4" />}
            />
          </StaggerItem>
          <StaggerItem>
            <StatCard
              label="Avg saved per decision"
              value={<AnimatedNumber value={744} format={(n) => inr(Math.round(n))} />}
              sub="Best: ₹4,120 on a laptop"
              icon={<Sparkles className="h-4 w-4" />}
            />
          </StaggerItem>
          <StaggerItem>
            <StatCard
              label="CO₂ avoided"
              value="48.2 kg"
              sub="Greener rides & bundled orders"
              delta="+4.1 kg"
              icon={<Leaf className="h-4 w-4" />}
            />
          </StaggerItem>
        </Stagger>

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
          <Stagger scroll className="space-y-5">
            <StaggerItem>
              <Panel>
                <PanelHeader
                  title="Cumulative savings"
                  hint="Running total of verified savings across every accepted comparison this month."
                  action={<span className="text-xs text-muted-foreground">This month</span>}
                />
                <div className="mt-3 flex flex-wrap items-end gap-x-6 gap-y-2">
                  <span className="tc-num tc-display text-[30px] leading-none font-bold">
                    <AnimatedNumber value={31240} format={(n) => inr(Math.round(n))} />
                  </span>
                  <Tag tone="positive" icon={<ArrowUpRight className="h-3 w-3" />}>
                    18.4% vs last month
                  </Tag>
                </div>
                <TrendArea data={savingsTrend} format={(v) => `₹${Math.round(v / 1000)}k`} />
              </Panel>
            </StaggerItem>

            <StaggerItem>
              <Panel>
                <PanelHeader
                  title="Savings by month"
                  action={<span className="text-xs text-muted-foreground">Last 6 months</span>}
                />
                <TrendBars data={monthlySavings} format={(v) => `₹${Math.round(v / 1000)}k`} />
              </Panel>
            </StaggerItem>

            <StaggerItem>
              <Panel>
                <PanelHeader
                  title="Savings receipts"
                  icon={<Receipt className="h-4 w-4" />}
                  action={<span className="text-xs text-muted-foreground">Latest 4</span>}
                />
                <ul className="mt-2 divide-y divide-border">
                  {recentActivity.map((r) => (
                    <li
                      key={r.provider}
                      className="group -mx-2 grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 rounded-xl px-2 py-2.5 transition-colors hover:bg-surface-2"
                    >
                      <BrandLogo name={r.provider} size={32} />
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-semibold group-hover:text-brand">
                          {r.provider}
                        </p>
                        <p className="truncate text-[11px] text-muted-foreground">
                          {r.detail} · {r.time}
                        </p>
                      </div>
                      <div className="shrink-0 text-right">
                        <p className="tc-num text-[13px] font-semibold">{inr(r.amount)}</p>
                        <p className="tc-num text-[11px] font-semibold text-positive">
                          saved {inr(r.saved)}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              </Panel>
            </StaggerItem>
          </Stagger>

          <Stagger scroll className="space-y-5">
            <StaggerItem>
              <Panel>
                <PanelHeader title="By category" />
                <div className="mt-3 space-y-3.5">
                  {savingsByCategory.map((c) => (
                    <div key={c.label} className="group">
                      <div className="flex items-center justify-between text-[12px]">
                        <span className="font-medium group-hover:text-brand">{c.label}</span>
                        <span className="tc-num font-bold">{inr(c.value)}</span>
                      </div>
                      <span className="mt-1.5 block h-2 overflow-hidden rounded-full bg-muted">
                        <span
                          className="block h-full rounded-full bg-[image:var(--gradient-brand)] transition-all duration-700"
                          style={{ width: `${c.share * 100}%` }}
                        />
                      </span>
                      <p className="mt-1 text-[11px] text-muted-foreground">
                        {c.pct}% average discount vs default choice
                      </p>
                    </div>
                  ))}
                </div>
              </Panel>
            </StaggerItem>

            <StaggerItem>
              <Panel>
                <PanelHeader title="How we count it" />
                <div className="mt-2">
                  <KeyValue
                    rows={[
                      ["Decisions accepted", "42"],
                      ["Alternatives priced", "1,286"],
                      ["Verified savings", "₹31,240"],
                      ["Unverified (excluded)", "₹4,180"],
                    ]}
                  />
                </div>
                <p className="mt-3 border-t border-border pt-3 text-[11px] text-muted-foreground">
                  Savings equal the TrueCost of the option you'd have picked by default minus what you
                  actually paid.
                </p>
              </Panel>
            </StaggerItem>

            <StaggerItem>
              <Panel accent className="bg-brand-soft/40">
                <PanelHeader title="Always objective" icon={<Sparkles className="h-4 w-4" />} />
                <p className="mt-2 text-[12px] leading-relaxed text-muted-foreground">
                  We never favour a provider. Every rupee above is the difference between the default
                  option and the one your agent proved cheaper.
                </p>
              </Panel>
            </StaggerItem>
          </Stagger>
        </div>
      </div>
    </AppShell>
  );
}
