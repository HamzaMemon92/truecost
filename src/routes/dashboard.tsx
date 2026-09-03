import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowRight,
  ArrowUpRight,
  Bell,
  Car,
  Laptop,
  Leaf,
  MoreHorizontal,
  Plane,
  Settings2,
  ShieldCheck,
  ShoppingBasket,
  Sparkles,
  TrendingDown,
  UtensilsCrossed,
} from "lucide-react";
import { AppShell } from "@/components/tc/app-shell";
import { IntentInput } from "@/components/tc/intent-input";
import { BrandLogo } from "@/components/tc/brand-logo";
import {
  AnimatedNumber,
  CheckList,
  KeyValue,
  Panel,
  PanelHeader,
  ScoreRing,
  Stagger,
  StaggerItem,
  StatCard,
  Tag,
  statSparklines,
} from "@/components/tc/ui-kit";
import { Sparkline, TrendArea } from "@/components/tc/charts";
import {
  inr,
  recentActivity,
  recentIntents,
  recommendedActions,
  savingsByCategory,
  savingsTrend,
  trackedProducts,
  upcomingTrips,
  user,
} from "@/lib/mock-data";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Agent Dashboard — TrueCost" },
      {
        name: "description",
        content:
          "Your AI consumer agent's home base: verified savings, live price watches, category shortcuts and recommended next actions.",
      },
      { property: "og:title", content: "Agent Dashboard — TrueCost" },
      {
        property: "og:description",
        content: "Track verified savings, price watches and smart recommendations in one place.",
      },
    ],
  }),
  component: Dashboard,
});

/* ─── Category cards ─── */
const categories = [
  {
    label: "Products",
    sub: "412 tracked",
    icon: Laptop,
    iconBg: "bg-violet-100 text-violet-600",
    to: "/compare/product" as const,
  },
  {
    label: "Rides",
    sub: "8 providers",
    icon: Car,
    iconBg: "bg-blue-100 text-blue-600",
    to: "/compare/rides" as const,
  },
  {
    label: "Grocery",
    sub: "5 stores",
    icon: ShoppingBasket,
    iconBg: "bg-green-100 text-green-600",
    to: "/grocery" as const,
  },
  {
    label: "Travel",
    sub: "Flights & stays",
    icon: Plane,
    iconBg: "bg-indigo-100 text-indigo-600",
    to: "/travel" as const,
  },
  {
    label: "More categories",
    sub: "Explore all",
    icon: MoreHorizontal,
    iconBg: "bg-muted text-muted-foreground",
    to: "/compare" as const,
  },
];



/* ─── Recommended items with Lucide icons ─── */
const recommendedMeta = [
  { icon: Car,             color: "bg-blue-100 text-blue-600",   cta: "Compare" },
  { icon: ShoppingBasket,  color: "bg-orange-100 text-orange-600", cta: "View deals" },
  { icon: Bell,            color: "bg-purple-100 text-purple-600", cta: "Check now" },
];

/* ─── Time-aware greeting ─── */
function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

/* ─── Proactive NEXA alerts ─── */
const nexaAlerts = [
  {
    id: "alert-1",
    icon: Car,
    iconBg: "bg-blue-100 text-blue-600",
    label: "Uber surge now",
    message: "Ola is ₹43 cheaper right now. Surge ends in ~8 min.",
    cta: "Compare rides",
    href: "/compare/rides" as const,
    tone: "warning" as const,
  },
  {
    id: "alert-2",
    icon: UtensilsCrossed,
    iconBg: "bg-red-100 text-red-600",
    label: "Offer expiring",
    message: "₹80 off Domino's on Zomato — expires at 11 PM tonight.",
    cta: "Order now",
    href: "/food" as const,
    tone: "brand" as const,
  },
  {
    id: "alert-3",
    icon: Plane,
    iconBg: "bg-sky-100 text-sky-600",
    label: "Price drop",
    message: "IndiGo BLR→DEL dropped ₹800 since you searched 3 days ago.",
    cta: "View flights",
    href: "/travel" as const,
    tone: "positive" as const,
  },
];

function Dashboard() {
  return (
    <AppShell>
      <div className="space-y-5">

        {/* ═══════════════════════════════ HERO PANEL ═══════════════════════════════ */}
        <section className="relative isolate overflow-hidden rounded-2xl border border-border/60 bg-card shadow-[var(--elev-raised)]">
          {/* Full-width lavender bloom — matches reference exact */}
          <span
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(80%_180%_at_100%_-20%,oklch(0.88_0.06_270/0.55),transparent_60%)] bg-[radial-gradient(110%_160%_at_0%_-10%,oklch(0.90_0.04_280/0.30),transparent_50%)]"
          />
          <span
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(110%_140%_at_30%_-20%,color-mix(in_oklab,var(--color-brand)_10%,transparent),transparent_55%)]"
          />
          <span
            aria-hidden
            className="pointer-events-none absolute top-0 right-0 h-72 w-96 rounded-full bg-violet-300/15 blur-[90px]"
          />
          <span
            aria-hidden
            className="pointer-events-none absolute bottom-0 right-[20%] h-48 w-64 rounded-full bg-indigo-300/10 blur-[70px]"
          />
          <span aria-hidden className="tc-grain pointer-events-none absolute inset-0 opacity-40" />

          <div className="relative grid lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] lg:items-stretch">

            {/* ── Left: greeting + search ── */}
            <div className="min-w-0 px-6 py-5 sm:px-7 sm:py-6">
              <div className="flex items-center gap-2">
                <span className="flex h-2 w-2 rounded-full bg-positive shadow-[0_0_8px_var(--color-positive)]" />
                <span className="text-[12px] font-medium text-muted-foreground">
                  Agent online · 42 decisions this month
                </span>
              </div>
              <h1 className="tc-display mt-4 text-[30px] leading-tight font-bold tracking-[-0.04em] sm:text-[36px]">
                {getGreeting()}, {user.firstName}!
              </h1>
              <p className="mt-2 text-[14px] text-muted-foreground max-w-sm leading-relaxed">
                Your AI consumer agent finds the best value across everything.
              </p>
              <IntentInput className="mt-4 max-w-xl" />
            </div>

            {/* ── Center: Globe — fills the full column height like the reference ── */}
            <div className="relative hidden lg:block overflow-hidden">
              <img
                src="/2.png"
                alt="TrueCost AI Dashboard"
                className="tc-float absolute inset-0 h-full w-full object-contain object-center drop-shadow-2xl"
                style={{ transform: "scale(1.08)" }}
                loading="eager"
                decoding="async"
              />
            </div>

            {/* ── Right: DecisionScore ring + mini chart ── */}
            <div className="tc-glass hidden shrink-0 flex-col items-center justify-center gap-2.5 rounded-r-2xl border-l border-border/60 px-6 py-5 lg:flex" style={{ width: 230 }}>
              <ScoreRing score={9.1} size={88} />
              <div className="text-center">
                <p className="text-[12px] font-bold text-foreground">Avg DecisionScore</p>
                <p className="tc-num text-[10px] text-muted-foreground">Across 42 decisions</p>
              </div>
              <div className="flex items-end gap-[3px] h-9 w-full px-1">
                {[4, 6, 5, 8, 6, 9, 7, 10, 8, 9, 10, 9].map((h, i) => (
                  <span
                    key={i}
                    className="flex-1 rounded-sm"
                    style={{
                      height: `${h * 10}%`,
                      background: h >= 9
                        ? "var(--color-brand)"
                        : "color-mix(in oklab, var(--color-brand) 50%, transparent)",
                    }}
                  />
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground text-center leading-tight">
                Smarter choices.<br />A better you.
              </p>
            </div>
          </div>
        </section>

        {/* ═══════════════════════════ STAT CARDS (with sparklines) ═══════════════════════════ */}
        <Stagger className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StaggerItem>
            <StatCard
              label="Verified savings"
              value={<AnimatedNumber value={31240} format={(n) => inr(Math.round(n))} />}
              sub="Across 42 agent decisions"
              delta="+18.4% vs last month"
              deltaTone="positive"
              icon={<TrendingDown className="h-4 w-4" />}
              iconBg="bg-brand-soft text-brand"
              sparkData={statSparklines[0]}
              sparkTone="brand"
            />
          </StaggerItem>
          <StaggerItem>
            <StatCard
              label="Decisions this month"
              value={<AnimatedNumber value={42} />}
              sub="Avg DecisionScore 9.1 / 10"
              delta="+7 vs last month"
              icon={<Sparkles className="h-4 w-4" />}
              iconBg="bg-info-soft text-info"
              sparkData={statSparklines[1]}
              sparkTone="info"
            />
          </StaggerItem>
          <StaggerItem>
            <StatCard
              label="Active price watches"
              value={<AnimatedNumber value={14} />}
              sub="3 hit target price"
              delta="3 alerts"
              deltaTone="warning"
              icon={<Bell className="h-4 w-4" />}
              iconBg="bg-amber-soft text-amber"
              sparkData={statSparklines[2]}
              sparkTone="amber"
            />
          </StaggerItem>
          <StaggerItem>
            <StatCard
              label="CO₂ avoided"
              value="48.2 kg"
              sub="Greener rides & bundled orders"
              delta="+ 4.1 kg"
              deltaTone="positive"
              icon={<Leaf className="h-4 w-4" />}
              iconBg="bg-positive-soft text-positive"
              sparkData={statSparklines[3]}
              sparkTone="positive"
            />
          </StaggerItem>
        </Stagger>

        {/* ═══════════════════════ NEXA PROACTIVE ALERTS ═══════════════════════ */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-brand" />
            <p className="text-[13px] font-bold text-foreground">NEXA is watching for you</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            {nexaAlerts.map((alert) => {
              const AlertIcon = alert.icon;
              return (
                <div
                  key={alert.id}
                  className="flex items-start gap-3 rounded-xl border border-border bg-card p-4 transition-all hover:-translate-y-0.5 hover:shadow-sm"
                >
                  <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ${alert.iconBg}`}>
                    <AlertIcon className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{alert.label}</p>
                    <p className="mt-0.5 text-[12px] text-foreground leading-snug">{alert.message}</p>
                    <Link
                      to={alert.href}
                      className="mt-2 inline-flex items-center gap-1 text-[12px] font-bold text-brand hover:underline"
                    >
                      {alert.cta} <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ════════════════════════ START A COMPARISON ROW ════════════════════════ */}
        <Panel>
          <PanelHeader
            title="Start a comparison"
            action={
              <Link to="/compare" className="text-brand hover:underline text-sm font-medium flex items-center gap-1">
                All categories <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            }
          />
          <div className="mt-4 grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-5">
            {categories.map(({ label, sub, icon: Icon, iconBg, to }) => (
              <Link
                key={label}
                to={to}
                className="tc-ring group flex items-center justify-between gap-2.5 rounded-xl border border-border bg-surface-2/60 px-3.5 py-3 transition-all hover:-translate-y-0.5 hover:border-brand/25 hover:bg-brand-soft hover:shadow-[var(--elev-card)]"
              >
                <div className="flex items-center gap-2.5">
                  <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl text-sm ${iconBg}`}>
                    <Icon className="h-4 w-4" />
                  </span>
                  <div>
                    <p className="text-[13px] font-semibold leading-tight">{label}</p>
                    <p className="text-[11px] text-muted-foreground">{sub}</p>
                  </div>
                </div>
                <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-brand" />
              </Link>
            ))}
          </div>
        </Panel>

        {/* ════════════════════════ SAVINGS + RECOMMENDED GRID ════════════════════════ */}
        <Stagger scroll className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">

          {/* Savings chart */}
          <StaggerItem>
            <Panel className="h-full">
              <PanelHeader
                title="Verified savings"
                action={
                  <div className="flex items-center gap-1 rounded-lg border border-border bg-surface-2 p-0.5">
                    {["30D", "90D", "1Y"].map((t, i) => (
                      <span
                        key={t}
                        className={
                          i === 0
                            ? "rounded-md bg-card px-2 py-1 text-[11px] font-semibold text-foreground shadow-[var(--shadow-card)]"
                            : "cursor-pointer rounded-md px-2 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:text-foreground"
                        }
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                }
              />
              <div className="mt-3 flex flex-wrap items-end gap-x-4 gap-y-2">
                <span className="tc-num tc-display text-[30px] leading-none font-bold">
                  <AnimatedNumber value={31240} format={(n) => inr(Math.round(n))} />
                </span>
                <Tag tone="positive" icon={<ArrowUpRight className="h-3 w-3" />}>
                  18.4% vs last month
                </Tag>
              </div>
              <TrendArea data={savingsTrend} format={(v) => `₹${Math.round(v / 1000)}k`} />
              <div className="mt-3 grid grid-cols-2 gap-3 border-t border-border pt-3 sm:grid-cols-4">
                {savingsByCategory.map((c) => (
                  <div key={c.label}>
                    <p className="text-[11px] text-muted-foreground">{c.label}</p>
                    <p className="tc-num text-[15px] font-bold">{inr(c.value)}</p>
                    <span className="mt-1.5 block h-1 overflow-hidden rounded-full bg-muted">
                      <span
                        className="block h-full rounded-full bg-[image:var(--gradient-brand)] transition-all duration-500"
                        style={{ width: `${c.share * 100}%` }}
                      />
                    </span>
                  </div>
                ))}
              </div>
            </Panel>
          </StaggerItem>

          {/* Recommended for you — colored icons + pill buttons */}
          <StaggerItem>
            <Panel className="h-full">
              <PanelHeader title="Recommended for you" icon={<Sparkles className="h-4 w-4" />} />
              <ul className="mt-3 space-y-2.5">
                {recommendedActions.map((a, i) => {
                  const meta = recommendedMeta[i]!;
                  return (
                    <li
                      key={a.title}
                      className="flex items-center gap-3 rounded-xl border border-border bg-surface-2/40 p-3 transition-all hover:-translate-y-px hover:border-brand/20 hover:bg-brand-soft/30"
                    >
                      {/* Colored circular icon */}
                      <span
                        className={`grid h-10 w-10 shrink-0 place-items-center rounded-full ${meta.color}`}
                      >
                        <meta.icon className="h-5 w-5" />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-[13px] font-semibold leading-tight">{a.title}</p>
                        <p className="text-[11px] text-muted-foreground">{a.sub}</p>
                      </div>
                      <Link
                        to={a.href}
                        className="tc-ring flex shrink-0 items-center gap-1.5 rounded-lg bg-brand px-3 py-2 text-[12px] font-semibold text-brand-foreground transition-colors hover:bg-brand-strong"
                      >
                        {a.cta}
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </Panel>
          </StaggerItem>
        </Stagger>

        {/* ════════════════════════ BOTTOM GRID ════════════════════════ */}
        <Stagger scroll className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-6">

          {/* Price watches */}
          <StaggerItem className="xl:col-span-3">
            <Panel className="h-full">
              <PanelHeader
                title="Price watches"
                action={
                  <Link to="/watchlist" className="text-brand hover:underline text-sm">
                    Manage
                  </Link>
                }
              />
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                {trackedProducts.slice(0, 4).map((p) => (
                  <div
                    key={p.name}
                    className="rounded-xl border border-border bg-surface-2 p-3 transition-all hover:-translate-y-px hover:border-brand/25 hover:shadow-[var(--elev-card)]"
                  >
                    <div className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-start gap-2">
                      <BrandLogo name={p.seller} size={36} />
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-semibold">{p.name}</p>
                        <p className="truncate text-[11px] text-muted-foreground">{p.seller}</p>
                      </div>
                      <Tag tone={p.change < 0 ? "positive" : "danger"}>
                        {p.change < 0 ? "▼" : "▲"} {inr(Math.abs(p.change))}
                      </Tag>
                    </div>
                    <div className="mt-1 flex items-end justify-between gap-2">
                      <span className="tc-num text-lg font-bold">{inr(p.price)}</span>
                      <span className="text-[11px] text-muted-foreground">
                        Target {inr(p.target)}
                      </span>
                    </div>
                    <Sparkline data={p.history} tone={p.change < 0 ? "brand" : "danger"} />
                  </div>
                ))}
              </div>
            </Panel>
          </StaggerItem>

          {/* Recent agent activity */}
          <StaggerItem className="xl:col-span-3">
            <Panel className="h-full">
              <PanelHeader title="Recent agent activity" />
              <ul className="mt-2 divide-y divide-border">
                {recentActivity.map((r) => (
                  <li
                    key={r.provider}
                    className="-mx-2 flex items-center justify-between gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-surface-2"
                  >
                    <div className="flex min-w-0 items-center gap-2.5">
                      <BrandLogo name={r.provider} size={40} />
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-semibold">{r.provider}</p>
                        <p className="truncate text-[11px] text-muted-foreground">
                          {r.detail} · {r.time}
                        </p>
                      </div>
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

          {/* Saved preferences */}
          <StaggerItem className="xl:col-span-2">
            <Panel className="h-full">
              <PanelHeader title="Saved preferences" icon={<Settings2 className="h-4 w-4" />} />
              <div className="mt-3">
                <KeyValue
                  rows={[
                    ["Home", "Koramangala, Bengaluru"],
                    ["Budget style", "Value over speed"],
                    ["Payment", "ICICI Amazon Pay CC"],
                    ["Delivery window", "Before 9 PM"],
                    ["Sustainability", "Prefer greener option"],
                  ]}
                />
              </div>
            </Panel>
          </StaggerItem>

          {/* Upcoming */}
          <StaggerItem className="xl:col-span-2">
            <Panel className="h-full">
              <PanelHeader title="Upcoming" />
              <ul className="mt-3 space-y-2.5">
                {upcomingTrips.map((t) => (
                  <li
                    key={t.title}
                    className="-mx-2 flex items-center gap-3 rounded-lg px-2 py-1.5 transition-colors hover:bg-surface-2"
                  >
                    <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-soft leading-none text-brand-strong">
                      <span className="tc-num text-sm font-bold">{t.day}</span>
                      <span className="text-[9px] font-semibold">{t.month}</span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[13px] font-semibold">{t.title}</p>
                      <p className="truncate text-[11px] text-muted-foreground">
                        {t.sub} · {t.meta}
                      </p>
                    </div>
                    <BrandLogo name={t.sub} size={34} />
                  </li>
                ))}
              </ul>
            </Panel>
          </StaggerItem>

          {/* Recent intents */}
          <StaggerItem className="xl:col-span-2">
            <Panel className="h-full">
              <PanelHeader title="Recent intents" />
              <ul className="mt-2 divide-y divide-border">
                {recentIntents.map((item) => (
                  <li key={item.text}>
                    <Link
                      to={item.href}
                      className="group -mx-2 flex items-center justify-between gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-surface-2"
                    >
                      <span className="min-w-0">
                        <span className="block truncate text-[13px] font-medium group-hover:text-brand">
                          {item.text}
                        </span>
                        <span className="block truncate text-[11px] text-muted-foreground">
                          {item.meta}
                        </span>
                      </span>
                      <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-brand" />
                    </Link>
                  </li>
                ))}
              </ul>
            </Panel>
          </StaggerItem>

          {/* Trust */}
          <StaggerItem className="md:col-span-2 xl:col-span-6">
            <Panel accent className="bg-brand-soft/30">
              <PanelHeader title="Why trust the agent" icon={<ShieldCheck className="h-4 w-4" />} />
              <CheckList
                className="mt-3 sm:grid sm:grid-cols-2 sm:gap-x-6 sm:space-y-0 lg:grid-cols-4"
                items={[
                  "Every price is fee-inclusive TrueCost",
                  "No paid placement in rankings",
                  "Sources shown for each data point",
                  "Your preferences weight the score",
                ]}
              />
            </Panel>
          </StaggerItem>
        </Stagger>
      </div>
    </AppShell>
  );
}
