import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Bell, Eye, Target, TrendingDown } from "lucide-react";
import { AppShell } from "@/components/tc/app-shell";
import {
  EmptyState,
  Panel,
  PageHeader,
  PanelHeader,
  StatCard,
  Tag,
} from "@/components/tc/ui-kit";
import { BrandLogo } from "@/components/tc/brand-logo";
import { Sparkline } from "@/components/tc/charts";
import { riseIn, stagger } from "@/lib/motion";
import { inr, trackedProducts } from "@/lib/mock-data";

export const Route = createFileRoute("/watchlist")({
  head: () => ({
    meta: [
      { title: "Price Watchlist — TrueCost" },
      {
        name: "description",
        content:
          "Track target prices across products, flights and rides. Your agent alerts you the moment the TrueCost hits your target.",
      },
      { property: "og:title", content: "Price Watchlist — TrueCost" },
      {
        property: "og:description",
        content: "Target prices, drop alerts and 90-day price history for everything you're tracking.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Watchlist,
});

function Watchlist() {
  const items = trackedProducts;

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          eyebrow={<Tag tone="brand" icon={<Eye className="h-3 w-3" />}>Always watching</Tag>}
          title="Price watchlist"
          subtitle="14 items tracked across 6 sellers · checked every 15 minutes."
          actions={
            <button className="tc-ring flex items-center gap-1.5 rounded-xl bg-brand px-3.5 py-2 text-xs font-semibold text-brand-foreground shadow-[var(--shadow-glow)] transition-all hover:-translate-y-0.5 hover:bg-brand-strong">
              <Bell className="h-3.5 w-3.5" /> Add a watch
            </button>
          }
        />

        <section className="grid gap-4 sm:grid-cols-3">
          <StatCard label="Items tracked" value="14" sub="Across electronics & audio" icon={<Eye className="h-4 w-4" />} />
          <StatCard label="Hit target price" value="3" sub="Ready to buy now" delta="Act today" deltaTone="warning" icon={<Target className="h-4 w-4" />} />
          <StatCard label="Tracked drop value" value={inr(8590)} sub="Total price decline this month" delta="▼ 9.4%" icon={<TrendingDown className="h-4 w-4" />} />
        </section>

        {items.length === 0 ? (
          <EmptyState
            title="Nothing on watch yet"
            body="Add a product and your agent will monitor every seller, every 15 minutes, and ping you the moment it dips below your target."
            icon={<Eye className="h-5 w-5" />}
            action={
              <button className="rounded-xl bg-brand px-4 py-2 text-xs font-semibold text-brand-foreground">
                Add your first watch
              </button>
            }
          />
        ) : (
          <motion.div
            variants={stagger()}
            initial="hidden"
            animate="show"
            className="grid gap-4 lg:grid-cols-2"
          >
            {items.map((p) => {
              const hit = p.price <= p.target;
              return (
                <motion.div key={p.name} variants={riseIn}>
                  <Panel className="group h-full transition-all duration-300 hover:-translate-y-0.5 hover:border-brand/30 hover:shadow-[var(--elev-floating)]">
                    <div className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-start gap-3">
                      <BrandLogo name={p.seller} size={38} />
                      <div className="min-w-0">
                        <p className="tc-display truncate text-[15px] font-bold">{p.name}</p>
                        <p className="truncate text-[11px] text-muted-foreground">{p.seller}</p>
                      </div>
                      <Tag tone={p.change < 0 ? "positive" : "danger"}>
                        {p.change < 0 ? "▼" : "▲"} {inr(Math.abs(p.change))}
                      </Tag>
                    </div>

                    <div className="mt-4 flex flex-wrap items-end gap-x-4 gap-y-1">
                      <span className="tc-num tc-display text-[26px] leading-none font-bold">
                        {inr(p.price)}
                      </span>
                      <span className="text-[11px] text-muted-foreground">
                        Target <span className="tc-num font-semibold text-foreground">{inr(p.target)}</span>
                      </span>
                      {hit ? <Tag tone="positive">Target hit</Tag> : p.alert && <Tag tone="warning">Alert on</Tag>}
                    </div>

                    <div className="mt-1 opacity-90 transition-opacity group-hover:opacity-100">
                      <Sparkline data={p.history} tone={p.change < 0 ? "brand" : "danger"} />
                    </div>

                    <div className="mt-2">
                      <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                        <span>Progress to target</span>
                        <span className="tc-num font-semibold text-foreground">{p.progress}%</span>
                      </div>
                      <span className="mt-1.5 block h-1.5 overflow-hidden rounded-full bg-muted">
                        <motion.span
                          initial={{ width: 0 }}
                          whileInView={{ width: `${p.progress}%` }}
                          viewport={{ once: true }}
                          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                          className="block h-full rounded-full bg-gradient-to-r from-brand to-brand-strong"
                        />
                      </span>
                    </div>

                    <div className="mt-4 flex gap-2">
                      <button className="tc-ring flex-1 rounded-xl bg-brand px-3 py-2 text-[12px] font-semibold text-brand-foreground transition-colors hover:bg-brand-strong">
                        Compare sellers
                      </button>
                      <button className="tc-ring rounded-xl border border-border px-3 py-2 text-[12px] font-semibold transition-colors hover:border-brand/40 hover:text-brand">
                        Edit target
                      </button>
                    </div>
                  </Panel>
                </motion.div>
              );
            })}
          </motion.div>
        )}

        <Panel>
          <PanelHeader title="Recent alerts" />
          <ul className="mt-2 divide-y divide-border">
            {[
              ["iPhone 15 (128GB)", "Dropped ₹4,000 below target", "2 hours ago", "Amazon"],
              ["AirPods Pro (2nd Gen)", "Now ₹1,000 above target", "Yesterday", "Apple"],
              ["Sony WH-1000XM5", "New lowest price in 90 days", "3 days ago", "Sony"],
              ['LG 55" C4 OLED', "Price increased ₹2,400", "5 days ago", "LG"],
            ].map(([a, b, c, brand]) => (
              <li
                key={a}
                className="-mx-2 grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 rounded-xl px-2 py-3 transition-colors hover:bg-surface-2"
              >
                <BrandLogo name={brand!} size={30} />
                <div className="min-w-0">
                  <p className="truncate text-[13px] font-semibold">{a}</p>
                  <p className="truncate text-[11px] text-muted-foreground">{b}</p>
                </div>
                <span className="shrink-0 text-[11px] text-muted-foreground">{c}</span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </AppShell>
  );
}
