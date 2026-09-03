import { createFileRoute } from "@tanstack/react-router";
import {
  Bell,
  BadgeCheck,
  ChevronDown,
  CreditCard,
  Filter,
  Share2,
  ShieldCheck,
  Sparkles,
  Star,
} from "lucide-react";
import { AppShell } from "@/components/tc/app-shell";
import {
  CheckList,
  FactorBar,
  KeyValue,
  Panel,
  PageHeader,
  PanelHeader,
  ScoreRing,
  Tag,
} from "@/components/tc/ui-kit";
import { TrendArea } from "@/components/tc/charts";
import { cn } from "@/lib/utils";
import {
  inr,
  laptops,
  priceHistory,
  priceHistoryTicks,
  sellerComparison,
  whyWeRecommend,
} from "@/lib/mock-data";

export const Route = createFileRoute("/compare/product")({
  head: () => ({
    meta: [
      { title: "Laptop TrueCost Comparison — TrueCost" },
      {
        name: "description",
        content:
          "Compare laptops based on TrueCost including warranties, bundled offers and historical price trends.",
      },
      { property: "og:title", content: "Laptop TrueCost Comparison — TrueCost" },
      {
        property: "og:description",
        content: "Stop comparing sticker prices. Compare all-in TrueCost and DecisionScore.",
      },
    ],
  }),
  component: ProductCompare,
});

const specRows = [
  "Processor",
  "Memory",
  "Storage",
  "Display",
  "Battery Life",
  "Weight",
] as const;

function ProductCompare() {
  const best = laptops[0]!;

  return (
    <AppShell>
      <div className="space-y-5">
        <PageHeader
          eyebrow={
            <div className="flex flex-wrap items-center gap-2">
              <Tag tone="brand" icon={<Sparkles className="h-3 w-3" />}>
                Agent comparison
              </Tag>
              <span className="text-xs text-muted-foreground">
                Laptops · ₹75,000 – ₹1,40,000 · updated 4 min ago
              </span>
            </div>
          }
          title='Best 13" laptop for daily work + travel'
          subtitle="4 shortlisted from 38 configurations across 6 sellers."
          actions={
            <>
              <button className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-semibold text-muted-foreground transition-colors hover:text-foreground">
                <Filter className="h-3.5 w-3.5" /> Filters
              </button>
              <button className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-semibold text-muted-foreground transition-colors hover:text-foreground">
                <Share2 className="h-3.5 w-3.5" /> Share
              </button>
              <button className="flex items-center gap-1.5 rounded-lg bg-brand px-3 py-2 text-xs font-semibold text-brand-foreground transition-colors hover:bg-brand-strong">
                <Bell className="h-3.5 w-3.5" /> Track price
              </button>
            </>
          }
        />

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
          <div className="space-y-5">
            {/* Comparison matrix */}
            <Panel padded={false} className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[880px] border-collapse text-left">
                  <thead>
                    <tr>
                      <th className="tc-label sticky left-0 z-10 w-[168px] border-b border-border bg-card p-4 align-bottom">
                        Model
                      </th>
                      {laptops.map((l) => (
                        <th
                          key={l.id}
                          className={cn(
                            "border-b border-l border-border p-4 align-top",
                            l.recommended && "bg-brand-soft/60",
                          )}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <Tag tone={l.recommended ? "solid" : "neutral"}>
                              {l.recommended ? "Recommended" : l.priceLabel}
                            </Tag>
                            {l.recommended && <BadgeCheck className="h-4 w-4 text-brand" />}
                          </div>
                          <p className="mt-2.5 text-[14px] leading-snug font-bold">{l.name}</p>
                          <p className="text-[12px] text-muted-foreground">{l.sub}</p>
                          <p className="mt-1 text-[11px] text-muted-foreground">{l.config}</p>
                          <p className="tc-num mt-2.5 text-[19px] font-bold">{inr(l.price)}</p>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {specRows.map((row, i) => (
                      <tr key={row} className={i % 2 ? "bg-surface-2/60" : ""}>
                        <th className="sticky left-0 z-10 border-b border-border bg-inherit p-3.5 text-[12px] font-medium text-muted-foreground">
                          {row}
                        </th>
                        {laptops.map((l) => (
                          <td
                            key={l.id}
                            className={cn(
                              "border-b border-l border-border p-3.5 text-[13px] font-medium",
                              l.recommended && "bg-brand-soft/40",
                            )}
                          >
                            {l.specs[row]}
                          </td>
                        ))}
                      </tr>
                    ))}

                    <tr>
                      <th
                        colSpan={5}
                        className="border-b border-border bg-foreground/[0.03] p-3 text-left"
                      >
                        <span className="tc-label">TrueCost breakdown</span>
                      </th>
                    </tr>
                    {(
                      [
                        ["Base price", (l: typeof best) => inr(l.cost.base)],
                        ["Shipping", (l: typeof best) => l.cost.shipping],
                        ["Taxes (GST 18%)", (l: typeof best) => inr(l.cost.taxes)],
                        ["Extended warranty", (l: typeof best) => l.cost.warranty],
                      ] as const
                    ).map(([label, fn], i) => (
                      <tr key={label} className={i % 2 ? "bg-surface-2/60" : ""}>
                        <th className="sticky left-0 z-10 border-b border-border bg-inherit p-3.5 text-[12px] font-medium text-muted-foreground">
                          {label}
                        </th>
                        {laptops.map((l) => (
                          <td
                            key={l.id}
                            className={cn(
                              "tc-num border-b border-l border-border p-3.5 text-[13px] font-semibold",
                              l.recommended && "bg-brand-soft/40",
                            )}
                          >
                            {fn(l)}
                          </td>
                        ))}
                      </tr>
                    ))}
                    <tr className="bg-brand-soft/40">
                      <th className="sticky left-0 z-10 border-b border-border bg-brand-soft/60 p-3.5 text-[12px] font-bold">
                        TrueCost
                      </th>
                      {laptops.map((l) => (
                        <td
                          key={l.id}
                          className={cn(
                            "border-b border-l border-border p-3.5",
                            l.recommended && "bg-brand-soft/70",
                          )}
                        >
                          <p className="tc-num text-[17px] font-bold text-brand-strong">
                            {inr(l.cost.trueCost)}
                          </p>
                          {l.cost.advantage ? (
                            <p className="text-[11px] text-muted-foreground">
                              +{l.cost.advantage} vs best
                            </p>
                          ) : (
                            <p className="text-[11px] font-semibold text-positive">
                              Lowest TrueCost
                            </p>
                          )}
                        </td>
                      ))}
                    </tr>

                    <tr>
                      <th
                        colSpan={5}
                        className="border-b border-border bg-foreground/[0.03] p-3 text-left"
                      >
                        <span className="tc-label">Payment offers & EMI</span>
                      </th>
                    </tr>
                    <tr>
                      <th className="sticky left-0 z-10 border-b border-border bg-card p-3.5 text-[12px] font-medium text-muted-foreground">
                        Card offers
                      </th>
                      {laptops.map((l) => (
                        <td
                          key={l.id}
                          className={cn(
                            "space-y-1.5 border-b border-l border-border p-3.5",
                            l.recommended && "bg-brand-soft/40",
                          )}
                        >
                          <Tag tone="positive">{l.offers.card}</Tag>
                          <Tag tone="info">{l.offers.bank}</Tag>
                        </td>
                      ))}
                    </tr>
                    <tr className="bg-surface-2/60">
                      <th className="sticky left-0 z-10 border-b border-border bg-inherit p-3.5 text-[12px] font-medium text-muted-foreground">
                        EMI (12 / 24 mo)
                      </th>
                      {laptops.map((l) => (
                        <td
                          key={l.id}
                          className={cn(
                            "border-b border-l border-border p-3.5",
                            l.recommended && "bg-brand-soft/40",
                          )}
                        >
                          <p className="tc-num text-[13px] font-semibold">
                            {inr(l.emi.noCost)}
                            <span className="ml-1 text-[11px] font-normal text-muted-foreground">
                              no-cost
                            </span>
                          </p>
                          <p className="tc-num text-[12px] text-muted-foreground">
                            {inr(l.emi.low)} · 24 mo
                          </p>
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <th className="sticky left-0 z-10 border-border bg-card p-3.5 text-[12px] font-medium text-muted-foreground">
                        Seller trust
                      </th>
                      {laptops.map((l) => (
                        <td
                          key={l.id}
                          className={cn(
                            "border-l border-border p-3.5",
                            l.recommended && "bg-brand-soft/40",
                          )}
                        >
                          <div className="flex items-center gap-1.5">
                            <Star className="h-3.5 w-3.5 fill-warning text-warning" />
                            <span className="tc-num text-[13px] font-bold">{l.seller.score}</span>
                          </div>
                          <p className="text-[11px] text-muted-foreground">
                            {l.seller.name} · {l.seller.type}
                          </p>
                          <button className="mt-2.5 w-full rounded-lg bg-brand px-2 py-1.5 text-[11px] font-semibold text-brand-foreground transition-colors hover:bg-brand-strong">
                            View deal
                          </button>
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </Panel>

            {/* Seller spread */}
            <Panel>
              <PanelHeader
                title={`Where to buy the ${best.name}`}
                hint="Prices include shipping and applicable card offers."
                action={
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    Sort: TrueCost <ChevronDown className="h-3 w-3" />
                  </span>
                }
              />
              <ul className="mt-3 divide-y divide-border">
                {sellerComparison.map((s, i) => (
                  <li
                    key={s.seller}
                    className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 py-3 sm:flex sm:justify-between"
                  >
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-surface-2 text-[11px] font-bold">
                        {s.seller.slice(0, 2).toUpperCase()}
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-semibold">{s.seller}</p>
                        <p className="text-[11px] text-muted-foreground">
                          Trust {s.trust} · Delivers in 2 days
                        </p>
                      </div>
                      {i === 0 && <Tag tone="positive">Best price</Tag>}
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      <span className="tc-num text-[15px] font-bold">{inr(s.price)}</span>
                      <button className="rounded-lg border border-border px-2.5 py-1.5 text-[11px] font-semibold transition-colors hover:border-brand/40 hover:text-brand">
                        Visit
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </Panel>
          </div>

          {/* Right rail */}
          <div className="space-y-5">
            <Panel className="border-brand/20">
              <div className="flex items-start gap-3">
                <ScoreRing score={9.4} size={72} label="score" />
                <div className="min-w-0">
                  <p className="tc-label">DecisionScore</p>
                  <p className="text-[15px] font-bold">{best.name}</p>
                  <p className="text-[12px] text-muted-foreground">
                    Highest weighted score across your priorities
                  </p>
                </div>
              </div>
              <div className="mt-4 space-y-2 border-t border-border pt-4">
                <FactorBar label="TrueCost value" value={96} />
                <FactorBar label="Performance" value={92} />
                <FactorBar label="Battery" value={98} />
                <FactorBar label="Portability" value={90} />
                <FactorBar label="Resale value" value={94} />
              </div>
            </Panel>

            <Panel>
              <PanelHeader title="Why we recommend it" icon={<Sparkles className="h-4 w-4" />} />
              <CheckList className="mt-3" items={whyWeRecommend} />
              <button className="mt-4 w-full rounded-xl bg-brand px-3 py-2.5 text-[13px] font-semibold text-brand-foreground transition-colors hover:bg-brand-strong">
                Buy at TrueCost {inr(best.cost.trueCost)}
              </button>
              <p className="mt-2 text-center text-[11px] text-muted-foreground">
                No paid placement · price verified 4 min ago
              </p>
            </Panel>

            <Panel>
              <PanelHeader
                title="Price history"
                action={<span className="text-xs text-muted-foreground">90 days</span>}
              />
              <div className="mt-2 flex items-end gap-3">
                <span className="tc-num text-xl font-bold">{inr(109900)}</span>
                <Tag tone="positive">▼ 7.2% from peak</Tag>
              </div>
              <TrendArea
                data={priceHistory}
                ticks={priceHistoryTicks}
                height={160}
                format={(v) => `₹${Math.round(v / 1000)}k`}
              />
              <div className="mt-2 grid grid-cols-3 gap-2 border-t border-border pt-3 text-center">
                {[
                  ["Lowest", inr(108600)],
                  ["Average", inr(113200)],
                  ["Highest", inr(119000)],
                ].map(([k, v]) => (
                  <div key={k}>
                    <p className="text-[11px] text-muted-foreground">{k}</p>
                    <p className="tc-num text-[13px] font-bold">{v}</p>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel>
              <PanelHeader title="Cost of ownership" icon={<ShieldCheck className="h-4 w-4" />} />
              <div className="mt-2">
                <KeyValue
                  rows={[
                    ["TrueCost today", inr(116545)],
                    ["AppleCare+ (2 yr)", inr(24900)],
                    ["Est. resale after 2 yr", `− ${inr(68000)}`],
                    ["Net 2-year cost", inr(73445)],
                  ]}
                  emphasizeLast
                />
              </div>
            </Panel>

            <Panel>
              <PanelHeader title="Payment plan" icon={<CreditCard className="h-4 w-4" />} />
              <div className="mt-3 space-y-2">
                {[
                  ["No-cost EMI · 12 mo", inr(9712), "0% interest"],
                  ["Low-cost EMI · 24 mo", inr(8317), "12.5% p.a."],
                  ["Pay in full", inr(116545), "Save ₹4,120"],
                ].map(([a, b, c]) => (
                  <div
                    key={a}
                    className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-2 rounded-xl border border-border p-3"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-[13px] font-semibold">{a}</p>
                      <p className="text-[11px] text-muted-foreground">{c}</p>
                    </div>
                    <span className="tc-num shrink-0 text-[14px] font-bold">{b}</span>
                  </div>
                ))}
              </div>
            </Panel>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
