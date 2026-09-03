import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle, PiggyBank, Package, ShieldCheck, Sparkles } from "lucide-react";
import { AppShell } from "@/components/tc/app-shell";
import { BrandLogo } from "@/components/tc/brand-logo";
import {
  KeyValue,
  Panel,
  PageHeader,
  PanelHeader,
  StatCard,
  Tag,
  type Tone,
} from "@/components/tc/ui-kit";
import { TrendArea, TrendBars } from "@/components/tc/charts";
import { inr, monthlySavings, ownedItems, resaleTrend, smartAlerts } from "@/lib/mock-data";

export const Route = createFileRoute("/ownership")({
  head: () => ({
    meta: [
      { title: "Ownership & Savings — TrueCost" },
      {
        name: "description",
        content: "Track warranties, expected resale values, and lifetime savings for your purchases.",
      },
      { property: "og:title", content: "Ownership & Savings — TrueCost" },
      {
        property: "og:description",
        content: "Track warranties, expected resale values, and lifetime savings for your purchases.",
      },
    ],
  }),
  component: Ownership,
});

const statusTone: Record<string, Tone> = {
  Protected: "positive",
  "Under Warranty": "info",
  "Price Drop Alert": "warning",
  "Return Eligible": "danger",
};

function Ownership() {
  const paid = ownedItems.reduce((a, b) => a + b.paid, 0);
  const value = ownedItems.reduce((a, b) => a + b.value, 0);
  const saved = ownedItems.reduce((a, b) => a + b.saved, 0);

  return (
    <AppShell>
      <div className="space-y-5">
        <PageHeader
          eyebrow={<Tag tone="brand" icon={<Sparkles className="h-3 w-3" />}>Post-purchase agent</Tag>}
          title="Ownership & savings"
          subtitle="Your agent keeps working after checkout — warranties, price drops and resale value."
        />

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Total savings locked in" value={inr(saved)} sub="Across 6 owned items" delta="+₹4,560" icon={<PiggyBank className="h-4 w-4" />} />
          <StatCard label="Portfolio spend" value={inr(paid)} sub="Lifetime purchases tracked" icon={<Package className="h-4 w-4" />} />
          <StatCard label="Estimated resale value" value={inr(value)} sub={`${Math.round((value / paid) * 100)}% of purchase price`} delta="+3.1%" icon={<ShieldCheck className="h-4 w-4" />} />
          <StatCard label="Active protections" value="4" sub="2 warranties expiring soon" delta="1 urgent" deltaTone="danger" icon={<AlertTriangle className="h-4 w-4" />} />
        </section>

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
          <div className="space-y-5">
            <Panel>
              <PanelHeader title="Savings over time" action={<span className="text-xs text-muted-foreground">Last 6 months</span>} />
              <TrendBars data={monthlySavings} format={(v) => `₹${Math.round(v / 1000)}k`} />
            </Panel>

            <Panel>
              <PanelHeader title="Your owned items" action={<span className="text-xs text-muted-foreground">{ownedItems.length} items</span>} />
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {ownedItems.map((it) => (
                  <article
                    key={it.name}
                    className="rounded-xl border border-border bg-surface-2 p-4 transition-all duration-300 hover:-translate-y-0.5 hover:border-brand/30 hover:bg-card hover:shadow-[var(--elev-floating)]"
                  >
                    <div className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-start gap-2.5">
                      <BrandLogo name={it.brand} size={34} />
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-bold">{it.name}</p>
                        <p className="truncate text-[11px] text-muted-foreground">
                          {it.brand} · {it.category}
                        </p>
                      </div>
                      <Tag tone={statusTone[it.status] ?? "neutral"}>{it.status}</Tag>
                    </div>

                    <div className="mt-3 border-t border-border pt-2">
                      <KeyValue
                        rows={[
                          ["Purchased", it.purchased],
                          ["Paid", inr(it.paid)],
                          ["Resale value", inr(it.value)],
                          ["Saved by agent", inr(it.saved)],
                        ]}
                        emphasizeLast
                      />
                    </div>
                  </article>
                ))}
              </div>
            </Panel>
          </div>

          <div className="space-y-5">
            <Panel>
              <PanelHeader title="Smart alerts" icon={<AlertTriangle className="h-4 w-4" />} />
              <ul className="mt-3 space-y-2.5">
                {smartAlerts.map((a) => (
                  <li key={a.title} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 rounded-xl border border-border p-3">
                    <div className="min-w-0">
                      <p className="truncate text-[13px] font-semibold">{a.title}</p>
                      <p className="truncate text-[11px] text-muted-foreground">{a.sub}</p>
                    </div>
                    <Tag tone={a.tone}>{a.cta}</Tag>
                  </li>
                ))}
              </ul>
            </Panel>

            <Panel>
              <PanelHeader title="Portfolio resale value" action={<span className="text-xs text-muted-foreground">10 weeks</span>} />
              <TrendArea data={resaleTrend} height={150} format={(v) => `₹${Math.round(v / 1000)}k`} />
            </Panel>

            <Panel>
              <PanelHeader title="Category spend" />
              <div className="mt-2">
                <KeyValue
                  rows={[
                    ["Electronics", inr(244800)],
                    ["Accessories", inr(63799)],
                    ["Appliances", inr(67899)],
                    ["Total", inr(paid)],
                  ]}
                  emphasizeLast
                />
              </div>
            </Panel>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
