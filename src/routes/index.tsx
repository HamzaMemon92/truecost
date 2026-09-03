import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  Building2,
  Car,
  Check,
  ChevronRight,
  Clock,
  Plane,
  ShieldCheck,
  ShoppingBasket,
  Sparkles,
  TrendingDown,
  UtensilsCrossed,
  Zap,
} from "lucide-react";
import { Logo } from "@/components/tc/logo";
import { IntentInput } from "@/components/tc/intent-input";
import { BrandLogo } from "@/components/tc/brand-logo";
import { AnimatedNumber, Stagger, StaggerItem, Tag } from "@/components/tc/ui-kit";
import { ease } from "@/lib/motion";
import { inr } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "TrueCost — Every price. Every platform. One truth." },
      {
        name: "description",
        content:
          "TrueCost compares prices across 50+ apps with fee-inclusive TrueCost. Never overpay again. Rides, flights, grocery, food, hotels, shopping — all in one place.",
      },
      { property: "og:title", content: "TrueCost — Every price. Every platform. One truth." },
    ],
  }),
  component: Landing,
});

/* ── Data ── */
const marketplaces = [
  "Amazon", "Flipkart", "Uber", "Ola", "Rapido",
  "Blinkit", "Zepto", "Swiggy", "Zomato", "BigBasket",
  "IndiGo", "Air India", "MakeMyTrip", "Booking.com", "Airbnb",
  "Samsung", "Apple", "Croma",
];

const categories = [
  { label: "Rides",    icon: Car,             gradient: "from-zinc-100 to-slate-200",     iconColor: "text-zinc-700",    to: "/compare/rides", tagline: "Uber vs Ola vs Rapido" },
  { label: "Flights",  icon: Plane,           gradient: "from-sky-100 to-blue-200",       iconColor: "text-sky-600",     to: "/travel",        tagline: "All airlines compared" },
  { label: "Grocery",  icon: ShoppingBasket,  gradient: "from-green-100 to-emerald-200",  iconColor: "text-emerald-600", to: "/grocery",       tagline: "Blinkit vs Zepto vs Instamart" },
  { label: "Hotels",   icon: Building2,       gradient: "from-amber-100 to-orange-200",   iconColor: "text-amber-600",   to: "/hotels",        tagline: "All platforms compared" },
  { label: "Food",     icon: UtensilsCrossed, gradient: "from-red-100 to-rose-200",       iconColor: "text-rose-600",    to: "/food",          tagline: "Swiggy vs Zomato" },
  { label: "Shopping", icon: ShoppingBasket,  gradient: "from-violet-100 to-purple-200",  iconColor: "text-violet-600",  to: "/shopping",      tagline: "Amazon vs Flipkart" },
];

/* ── Live demo data ── */
const demoTabs = [
  {
    id: "rides",
    label: "Rides",
    icon: Car,
    route: "Koramangala → Airport",
    providers: [
      { name: "Uber Go",      price: 310, eta: "4 min", score: 88, pick: false },
      { name: "Ola Prime",    price: 286, eta: "6 min", score: 94, pick: true  },
      { name: "Rapido Auto",  price: 249, eta: "3 min", score: 82, pick: false },
    ],
    insight: "Ola Prime is ₹23 more than Rapido but 4.8★ reliable on this route.",
  },
  {
    id: "food",
    label: "Food",
    icon: UtensilsCrossed,
    route: "Domino's Margherita Pizza",
    providers: [
      { name: "Swiggy", price: 294, eta: "35 min", score: 86, pick: true  },
      { name: "Zomato", price: 314, eta: "40 min", score: 79, pick: false },
    ],
    insight: "Swiggy is ₹20 cheaper with free delivery today. Order from Swiggy.",
  },
  {
    id: "grocery",
    label: "Grocery",
    icon: ShoppingBasket,
    route: "Weekly basket (12 items)",
    providers: [
      { name: "Blinkit",  price: 1248, eta: "9 min",  score: 91, pick: false },
      { name: "Zepto",    price: 1184, eta: "14 min", score: 88, pick: true  },
      { name: "Instamart",price: 1302, eta: "20 min", score: 74, pick: false },
    ],
    insight: "Zepto saves ₹64 vs Blinkit. Split order saves extra ₹38.",
  },
  {
    id: "flights",
    label: "Flights",
    icon: Plane,
    route: "BLR → DEL · 24 May",
    providers: [
      { name: "IndiGo 6E-431", price: 4299, eta: "06:15–09:00", score: 93, pick: true  },
      { name: "SpiceJet SG-123",price: 3899, eta: "11:30–14:15", score: 87, pick: false },
      { name: "Air India AI-130",price: 5199, eta: "07:00–09:45", score: 89, pick: false },
    ],
    insight: "IndiGo scores best: 98% on-time rate on this route. Best overall value.",
  },
];

/* ── Floating comparison card data ── */
const floatingCards = [
  {
    id: 1,
    label: "Rides saved",
    left: "Uber ₹310",
    right: "Ola ₹286 ✓",
    saved: "₹24 saved",
    tone: "brand" as const,
    style: { top: "8%", right: "-6%" },
    delay: 0.4,
  },
  {
    id: 2,
    label: "Food order",
    left: "Zomato ₹439",
    right: "Swiggy ₹404 ✓",
    saved: "₹35 saved",
    tone: "positive" as const,
    style: { bottom: "18%", left: "-8%" },
    delay: 0.6,
  },
  {
    id: 3,
    label: "BLR → DEL",
    left: "₹5,199",
    right: "₹4,299 ✓",
    saved: "₹900 saved",
    tone: "gold" as const,
    style: { top: "45%", right: "-14%" },
    delay: 0.8,
  },
];

function Landing() {
  const [activeDemo, setActiveDemo] = useState("rides");
  const demo = demoTabs.find((t) => t.id === activeDemo)!;

  return (
    <div className="min-h-screen bg-background">

      {/* ─── Header ─── */}
      <header className="tc-glass sticky top-0 z-30 border-b border-border/70">
        <div className="mx-auto flex h-16 max-w-[1200px] items-center gap-4 px-4 sm:px-6">
          <Logo size="md" />
          <nav className="ml-6 hidden items-center gap-6 text-[13px] font-medium text-muted-foreground md:flex">
            {(
              [
                { label: "Compare", to: "/compare" },
                { label: "Grocery", to: "/grocery" },
                { label: "Travel", to: "/travel" },
                { label: "Savings", to: "/savings" },
              ] as const
            ).map(({ label, to }) => (
              <Link key={label} to={to} className="transition-colors hover:text-foreground">
                {label}
              </Link>
            ))}
          </nav>
          <Link
            to="/dashboard"
            className="tc-ring ml-auto flex items-center gap-1.5 rounded-full bg-brand px-4 py-2 text-[13px] font-semibold text-brand-foreground shadow-[var(--shadow-glow)] transition-all hover:-translate-y-px hover:bg-brand-strong"
          >
            Open agent <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </header>

      <main>

        {/* ═══════════════════════════ HERO ═══════════════════════════ */}
        <section className="dark relative isolate overflow-hidden bg-background text-foreground">
          {/* Atmospheric depth */}
          <span aria-hidden className="pointer-events-none absolute inset-0 bg-[radial-gradient(120%_100%_at_15%_-10%,color-mix(in_oklab,var(--color-brand)_28%,transparent),transparent_60%)]" />
          <span aria-hidden className="pointer-events-none absolute -top-40 right-[-10%] h-[520px] w-[520px] rounded-full bg-teal/20 blur-[120px]" />
          <span aria-hidden className="pointer-events-none absolute bottom-[-30%] left-[-10%] h-[460px] w-[460px] rounded-full bg-brand/15 blur-[130px]" />
          <span aria-hidden className="tc-grain pointer-events-none absolute inset-0" />
          <span aria-hidden className="pointer-events-none absolute inset-0 opacity-[0.06] [background-image:linear-gradient(var(--color-foreground)_1px,transparent_1px),linear-gradient(90deg,var(--color-foreground)_1px,transparent_1px)] [background-size:64px_64px] [mask-image:radial-gradient(75%_60%_at_50%_0%,black,transparent)]" />

          <div className="relative mx-auto grid max-w-[1200px] gap-12 px-4 py-20 sm:px-6 lg:grid-cols-[minmax(0,1fr)_430px] lg:items-center lg:py-28">

            {/* Left: headline */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={ease}
              className="min-w-0"
            >
              <Tag tone="brand" icon={<Sparkles className="h-3.5 w-3.5" />} className="px-3 py-1 text-[11px] font-bold uppercase tracking-[0.15em]">
                TrueCost AI Agent
              </Tag>
              <h1 className="tc-display mt-6 text-[52px] leading-[1.05] font-black tracking-[-0.05em] sm:text-[72px] lg:text-[84px]">
                Every price.<br />
                <span className="bg-[image:linear-gradient(100deg,var(--color-brand),var(--color-teal)_65%,var(--color-gold))] bg-clip-text text-transparent">
                  One truth.
                </span>
              </h1>
              <p className="mt-6 max-w-xl text-[17px] leading-[1.6] text-muted-foreground/90 font-medium sm:text-[19px]">
                TrueCost AI compares 50+ apps — taxes, fees, surge, delivery all included — and tells you exactly where to buy, book, or order.
              </p>
              <IntentInput className="mt-10 max-w-xl" />
              <div className="mt-8 flex flex-wrap gap-x-7 gap-y-2 text-[13px] text-muted-foreground">
                {["No paid placement", "Fee-inclusive TrueCost", "50+ apps compared"].map((t) => (
                  <span key={t} className="flex items-center gap-1.5">
                    <Check className="h-3.5 w-3.5 text-brand" strokeWidth={3} />
                    {t}
                  </span>
                ))}
              </div>

              {/* Live stats */}
              <div className="mt-10 grid grid-cols-3 gap-4 border-t border-border/60 pt-8 sm:flex sm:flex-wrap sm:gap-10">
                {[
                  { value: 47284, label: "decisions today", prefix: "" },
                  { value: 31240, label: "avg monthly savings", prefix: "₹" },
                  { value: 50, label: "apps connected", prefix: "" },
                ].map((s) => (
                  <div key={s.label} className="min-w-0">
                    <p className="tc-num text-[20px] font-black tracking-tight text-foreground sm:text-[28px]">
                      {s.prefix}<AnimatedNumber value={s.value} format={(n) => Math.round(n).toLocaleString("en-IN")} />
                      {s.value === 50 && "+"}
                    </p>
                    <p className="mt-1 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/70 sm:text-[12px]">
                      {s.label}
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Right: globe + floating comparison cards */}
            <motion.div
              initial={{ opacity: 0, y: 26 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...ease, delay: 0.12 }}
              className="relative flex items-center justify-center"
            >
              <span aria-hidden className="absolute -inset-8 rounded-full bg-brand/10 blur-3xl" />

              {/* Globe */}
              <img
                src="/hero-globe.png"
                alt="TrueCost compares across all platforms"
                className="tc-float relative z-10 w-full max-w-[430px] object-contain mix-blend-screen [mask-image:radial-gradient(circle_at_center,black_60%,transparent_85%)]"
                loading="eager"
                decoding="async"
              />

              {/* Floating comparison cards */}
              {floatingCards.map((card) => (
                <motion.div
                  key={card.id}
                  initial={{ opacity: 0, scale: 0.85, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  transition={{ ...ease, delay: card.delay }}
                  className="absolute z-20 hidden sm:block"
                  style={card.style}
                >
                  <div className="w-[220px] overflow-hidden rounded-2xl border border-white/10 bg-background/60 p-3.5 shadow-[0_12px_40px_rgba(0,0,0,0.5)] backdrop-blur-2xl">
                    <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground/90">{card.label}</p>
                    <div className="mt-2 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-[12px] font-medium text-muted-foreground">{card.left}</span>
                      </div>
                      <div className="flex items-center justify-between gap-1.5 rounded-lg bg-brand-soft/20 px-2.5 py-1.5 border border-brand/10">
                        <span className="text-[12px] font-bold text-brand whitespace-nowrap">{card.right}</span>
                        <span className="shrink-0 text-[10px] font-bold text-positive whitespace-nowrap">{card.saved}</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ═══════════════════ BRAND MARQUEE ═══════════════════ */}
        <section className="border-y border-border bg-surface-2/60 py-8">
          <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
            <p className="text-center text-[11px] font-semibold tracking-[0.16em] text-muted-foreground uppercase">
              Live pricing across the apps you actually use
            </p>
            <Stagger scroll delay={0.03} className="mt-5 flex flex-wrap items-center justify-center gap-2">
              {marketplaces.map((m) => (
                <StaggerItem key={m}>
                  <span className="tc-lift flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5">
                    <BrandLogo name={m} size={18} rounded="rounded-full" className="border-0" />
                    <span className="text-[12px] font-semibold text-muted-foreground">{m}</span>
                  </span>
                </StaggerItem>
              ))}
            </Stagger>
          </div>
        </section>

        {/* ═══════════════════ LIVE DEMO — "See it in action" ═══════════════════ */}
        <section className="mx-auto max-w-[1200px] px-4 py-20 sm:px-6">
          <div className="mb-10 text-center">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-brand">See it in action</p>
            <h2 className="tc-display mt-3 text-[32px] font-bold tracking-tight sm:text-[40px]">
              Compare anything in seconds
            </h2>
            <p className="mt-3 text-[15px] text-muted-foreground">
              NEXA shows the real total — not the marketing price
            </p>
          </div>

          {/* Tab selector */}
          <div className="flex justify-center">
            <div className="inline-flex rounded-2xl border border-border bg-surface-2/60 p-1.5 gap-1">
              {demoTabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveDemo(tab.id)}
                    className={cn(
                      "flex items-center gap-2 rounded-xl px-4 py-2.5 text-[13px] font-semibold transition-all",
                      activeDemo === tab.id
                        ? "bg-card text-foreground shadow-[var(--elev-card)]"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    <Icon className={cn("h-4 w-4", activeDemo === tab.id ? "text-brand" : "")} />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Demo content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeDemo}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
              className="mx-auto mt-6 max-w-2xl"
            >
              <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-[var(--elev-raised)]">
                {/* Demo header */}
                <div className="flex items-center gap-3 border-b border-border bg-surface-2/40 px-5 py-3">
                  <div className="flex gap-1.5">
                    <div className="h-3 w-3 rounded-full bg-red-400/60" />
                    <div className="h-3 w-3 rounded-full bg-amber-400/60" />
                    <div className="h-3 w-3 rounded-full bg-green-400/60" />
                  </div>
                  <span className="text-[12px] font-medium text-muted-foreground">{demo.route}</span>
                </div>

                <div className="p-5 space-y-3">
                  {/* NEXA insight */}
                  <div className="flex items-start gap-2.5 rounded-xl bg-brand-soft/30 border border-brand/15 p-3">
                    <Sparkles className="h-4 w-4 shrink-0 text-brand mt-0.5" />
                    <p className="text-[13px] text-foreground/90 leading-relaxed">
                      <span className="font-bold text-brand">NEXA: </span>{demo.insight}
                    </p>
                  </div>

                  {/* Provider rows */}
                  {demo.providers.map((p) => (
                    <div
                      key={p.name}
                      className={cn(
                        "flex items-center justify-between gap-4 rounded-xl border p-3.5 transition-all",
                        p.pick
                          ? "border-brand/25 bg-brand-soft/15 shadow-[var(--shadow-glow)]"
                          : "border-border bg-surface-2/40"
                      )}
                    >
                      <div className="flex items-center gap-3">
                        {p.pick && (
                          <div className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-brand">
                            <Check className="h-3 w-3 text-brand-foreground" strokeWidth={3} />
                          </div>
                        )}
                        <div>
                          <p className="text-[13px] font-bold">{p.name}</p>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <Clock className="h-3 w-3 text-muted-foreground" />
                            <span className="text-[11px] text-muted-foreground">{p.eta}</span>
                            {p.pick && <Tag tone="brand" className="text-[10px] ml-1">NEXA PICK</Tag>}
                          </div>
                        </div>
                      </div>
                      <p className={cn("tc-num text-[18px] font-bold", p.pick ? "text-brand" : "")}>
                        {inr(p.price)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </AnimatePresence>

          <div className="mt-8 text-center">
            <Link
              to="/compare"
              className="inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3 text-[14px] font-semibold text-brand-foreground shadow-[var(--shadow-glow)] transition-all hover:-translate-y-px hover:bg-brand-strong"
            >
              Try it yourself <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>

        {/* ═══════════════════ CATEGORY GRID ═══════════════════ */}
        <section className="bg-surface-2/40 py-20 border-y border-border">
          <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
            <div className="mb-10 text-center">
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-brand">Everything in one place</p>
              <h2 className="tc-display mt-3 text-[32px] font-bold tracking-tight sm:text-[40px]">
                6 categories. Infinite decisions.
              </h2>
            </div>
            <Stagger scroll className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
              {categories.map((cat) => {
                const Icon = cat.icon;
                return (
                  <StaggerItem key={cat.label}>
                    <Link
                      to={cat.to}
                      className="group flex flex-col rounded-2xl border border-border bg-card p-4 transition-all hover:-translate-y-1 hover:border-brand/20 hover:shadow-md"
                    >
                      <div className={`mb-3 flex h-14 items-center justify-center rounded-xl bg-gradient-to-br ${cat.gradient}`}>
                        <Icon className={`h-7 w-7 transition-transform duration-300 group-hover:scale-110 ${cat.iconColor}`} />
                      </div>
                      <p className="text-[14px] font-bold">{cat.label}</p>
                      <p className="mt-0.5 text-[11px] text-muted-foreground leading-tight">{cat.tagline}</p>
                      <ChevronRight className="mt-2 h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-brand" />
                    </Link>
                  </StaggerItem>
                );
              })}
            </Stagger>
          </div>
        </section>

        {/* ═══════════════════ 3 PILLARS ═══════════════════ */}
        <section className="mx-auto max-w-[1200px] px-4 py-20 sm:px-6">
          <Stagger scroll className="grid gap-4 lg:grid-cols-3">
            {[
              {
                title: "TrueCost",
                body: "Sticker price is marketing. TrueCost adds taxes, delivery, fees, surge and subtracts real offers you qualify for.",
                icon: <ShieldCheck className="h-5 w-5" />,
                color: "bg-brand-soft text-brand",
              },
              {
                title: "DecisionScore",
                body: "A 0–10 score weighted by your priorities — value, speed, reliability, sustainability — with every factor shown.",
                icon: <Sparkles className="h-5 w-5" />,
                color: "bg-info-soft text-info",
              },
              {
                title: "Post-purchase agent",
                body: "Warranties, return windows, price-drop refunds and resale value tracked long after checkout.",
                icon: <TrendingDown className="h-5 w-5" />,
                color: "bg-positive-soft text-positive",
              },
            ].map((c) => (
              <StaggerItem key={c.title}>
                <div className="tc-card tc-lift group h-full p-6">
                  <span className={`grid h-10 w-10 place-items-center rounded-xl transition-transform duration-300 group-hover:scale-105 ${c.color}`}>
                    {c.icon}
                  </span>
                  <h2 className="tc-display mt-4 text-[18px] font-bold">{c.title}</h2>
                  <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">{c.body}</p>
                </div>
              </StaggerItem>
            ))}
          </Stagger>

          {/* Stats strip */}
          <div className="tc-card mt-5 grid gap-6 p-8 sm:grid-cols-3 sm:p-10">
            {[
              { v: 31240,  prefix: "₹", suffix: "",  label: "Average verified savings per member, per month" },
              { v: 50,     prefix: "",  suffix: "+",  label: "Apps and platforms priced in real time" },
              { v: 1.4,    prefix: "",  suffix: "s",  label: "Median time to a ranked recommendation" },
            ].map((s) => (
              <div key={s.label}>
                <p className="tc-num tc-display text-[34px] leading-none font-bold text-brand-strong">
                  {s.prefix}
                  <AnimatedNumber
                    value={s.v}
                    format={(n) => s.suffix === "s" ? n.toFixed(1) : Math.round(n).toLocaleString("en-IN")}
                  />
                  {s.suffix}
                </p>
                <p className="mt-2 text-[13px] text-muted-foreground">{s.label}</p>
              </div>
            ))}
          </div>

          {/* How it works — 3 steps */}
          <div className="mt-5 rounded-2xl border border-border bg-surface-2/60 p-8">
            <p className="text-center text-[11px] font-bold uppercase tracking-[0.16em] text-muted-foreground">How it works</p>
            <div className="mt-6 grid gap-6 sm:grid-cols-3">
              {[
                { step: "01", title: "Tell NEXA what you need", body: "Search a product, destination, dish or route in plain language." },
                { step: "02", title: "NEXA prices every option", body: "Fees, surge, delivery, taxes — all included. No hidden costs." },
                { step: "03", title: "You get one clear answer", body: "The best option highlighted with full reasoning. No guesswork." },
              ].map((s) => (
                <div key={s.step} className="flex gap-4">
                  <span className="tc-num shrink-0 text-[28px] font-black text-brand/20">{s.step}</span>
                  <div>
                    <p className="text-[14px] font-bold">{s.title}</p>
                    <p className="mt-1 text-[13px] text-muted-foreground leading-relaxed">{s.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Dark CTA */}
          <div className="dark relative mt-5 overflow-hidden rounded-3xl border border-border bg-background px-6 py-16 text-center text-foreground">
            <span aria-hidden className="pointer-events-none absolute inset-0 bg-[radial-gradient(90%_120%_at_50%_0%,color-mix(in_oklab,var(--color-brand)_26%,transparent),transparent_65%)]" />
            <span aria-hidden className="tc-grain pointer-events-none absolute inset-0" />
            <div className="relative flex flex-col items-center gap-4">
              <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-[12px]">
                <Zap className="h-3.5 w-3.5 text-brand" />
                <span className="text-muted-foreground">Free to use · No account required to compare</span>
              </div>
              <h2 className="tc-display max-w-xl text-[30px] leading-tight font-bold tracking-[-0.035em] sm:text-[38px]">
                Stop guessing what things really cost.
              </h2>
              <p className="max-w-md text-[14px] text-muted-foreground">
                Open the agent and watch it price your next decision end to end.
              </p>
              <Link
                to="/dashboard"
                className="tc-ring mt-1 flex items-center gap-1.5 rounded-full bg-brand px-6 py-3 text-[14px] font-semibold text-brand-foreground shadow-[var(--shadow-glow)] transition-all hover:-translate-y-px hover:bg-brand-strong"
              >
                Open your dashboard <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="mx-auto flex max-w-[1200px] flex-col items-center gap-3 px-4 text-center sm:flex-row sm:justify-between sm:px-6 sm:text-left">
          <Logo size="sm" />
          <p className="text-[12px] text-muted-foreground">
            © 2025 TrueCost · AI Consumer Agent · Prototype with illustrative data
          </p>
        </div>
      </footer>
    </div>
  );
}
