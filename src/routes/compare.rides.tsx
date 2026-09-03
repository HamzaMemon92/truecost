import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  ArrowUpDown,
  Clock,
  Edit2,
  Info,
  MapPin,
  Navigation,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";
import { AppShell } from "@/components/tc/app-shell";
import { Panel, Tag, Stagger, StaggerItem, TrueCostBar } from "@/components/tc/ui-kit";
import { inr } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/compare/rides")({
  head: () => ({
    meta: [{ title: "Compare Rides — TrueCost" }],
  }),
  component: RideCompare,
});

/* ── Provider data ── */
const providers = [
  {
    id: "uber-go",
    name: "Uber Go",
    initial: "U",
    color: "bg-zinc-900 text-white",
    accent: "border-l-zinc-900",
    type: "Sedan",
    eta: 4,
    price: 310,
    score: 88,
    recommended: false,
    cheapest: false,
  },
  {
    id: "ola-prime",
    name: "Ola Prime",
    initial: "O",
    color: "bg-emerald-600 text-white",
    accent: "border-l-emerald-500",
    type: "SUV",
    eta: 6,
    price: 286,
    score: 94,
    recommended: true,
    cheapest: false,
    quote: "₹23 more than Rapido but 3 min faster with 4.8★ reliability on this route",
  },
  {
    id: "rapido",
    name: "Rapido",
    initial: "R",
    color: "bg-amber-500 text-white",
    accent: "border-l-amber-400",
    type: "Auto",
    eta: 3,
    price: 249,
    score: 82,
    recommended: false,
    cheapest: false,
  },
  {
    id: "uber-auto",
    name: "Uber Auto",
    initial: "U",
    color: "bg-zinc-900 text-white",
    accent: "border-l-zinc-700",
    type: "Auto",
    eta: 5,
    price: 239,
    score: 79,
    recommended: false,
    cheapest: true,
  },
];

const quickRoutes = [
  { label: "Home → Office", from: "HSR Layout, Bangalore", to: "Whitefield, Bangalore" },
  { label: "Airport Run", from: "Koramangala, Bangalore", to: "Kempegowda Airport (BLR)" },
  { label: "Railway Station", from: "Koramangala, Bangalore", to: "KSR Bengaluru City Junction" },
];

const filters = ["Cheapest", "Fastest", "Best rated"] as const;

function RideCompare() {
  const [phase, setPhase] = useState<"input" | "results">("input");
  const [from, setFrom] = useState("Koramangala, Bangalore");
  const [to, setTo] = useState("");
  const [pax, setPax] = useState(1);
  const [when, setWhen] = useState<"Now" | "Schedule">("Now");
  const [activeFilter, setActiveFilter] = useState<string>("Best rated");

  const recommended = providers.find((p) => p.recommended)!;

  const sorted = [...providers].sort((a, b) => {
    if (activeFilter === "Cheapest") return a.price - b.price;
    if (activeFilter === "Fastest") return a.eta - b.eta;
    return b.score - a.score;
  });

  return (
    <AppShell>
      <AnimatePresence mode="wait">
        {/* ═══ INPUT STATE ═══ */}
        {phase === "input" && (
          <motion.div
            key="input"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12, scale: 0.98 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            className="flex min-h-[80vh] flex-col items-center justify-center px-4 py-12"
          >
            {/* Header */}
            <div className="mb-10 text-center">
              <p className="mb-3 text-[11px] font-bold uppercase tracking-[0.18em] text-brand">
                Rides
              </p>
              <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
                Find your best ride
              </h1>
              <p className="mt-3 text-[15px] text-muted-foreground">
                Compare Uber, Ola, Rapido & more — NEXA picks the smartest option
              </p>
            </div>

            {/* Route card */}
            <div className="w-full max-w-md">
              <Panel elevation="raised" className="overflow-hidden">
                {/* FROM / TO with dashed connector */}
                <div className="relative space-y-0 p-5">
                  {/* FROM */}
                  <div className="flex items-center gap-3 rounded-xl bg-surface-2/60 px-4 py-3.5 ring-1 ring-transparent transition-all focus-within:ring-brand/30">
                    <div className="flex h-2.5 w-2.5 shrink-0 items-center justify-center rounded-full bg-brand shadow-[0_0_8px_var(--color-brand)]" />
                    <input
                      type="text"
                      value={from}
                      onChange={(e) => setFrom(e.target.value)}
                      className="flex-1 bg-transparent text-[14px] font-semibold text-foreground outline-none placeholder:text-muted-foreground/50"
                      placeholder="From"
                    />
                    <MapPin className="h-3.5 w-3.5 shrink-0 text-muted-foreground/50" />
                  </div>

                  {/* Dashed connector + swap button */}
                  <div className="relative flex items-center py-1">
                    <div className="ml-[18px] flex flex-col gap-[3px]">
                      {Array(4).fill(0).map((_, i) => (
                        <div key={i} className="h-[3px] w-[3px] rounded-full bg-border" />
                      ))}
                    </div>
                    <button
                      onClick={() => { const t = from; setFrom(to); setTo(t); }}
                      className="absolute right-3 top-1/2 -translate-y-1/2 grid h-7 w-7 place-items-center rounded-full border border-border bg-card text-muted-foreground shadow-sm transition-all hover:border-brand/40 hover:text-brand active:scale-90"
                    >
                      <ArrowUpDown className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  {/* TO */}
                  <div className="flex items-center gap-3 rounded-xl bg-surface-2/60 px-4 py-3.5 ring-1 ring-transparent transition-all focus-within:ring-brand/30">
                    <Navigation className="h-3 w-3 shrink-0 text-foreground/60" />
                    <input
                      type="text"
                      value={to}
                      onChange={(e) => setTo(e.target.value)}
                      placeholder="Where to?"
                      className="flex-1 bg-transparent text-[14px] font-semibold text-foreground outline-none placeholder:text-muted-foreground/50"
                    />
                  </div>
                </div>

                {/* When + passengers row */}
                <div className="flex items-center gap-3 border-t border-border/60 px-5 py-3">
                  {/* When toggle */}
                  <div className="flex rounded-lg border border-border bg-surface-2/40 p-0.5">
                    {(["Now", "Schedule"] as const).map((w) => (
                      <button
                        key={w}
                        onClick={() => setWhen(w)}
                        className={cn(
                          "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[12px] font-semibold transition-all",
                          when === w
                            ? "bg-card text-foreground shadow-sm"
                            : "text-muted-foreground hover:text-foreground"
                        )}
                      >
                        {w === "Now" && <Zap className="h-3 w-3" />}
                        {w}
                      </button>
                    ))}
                  </div>

                  {/* Passenger counter */}
                  <div className="flex items-center gap-1 rounded-lg border border-border bg-surface-2/40 p-0.5">
                    <Users className="ml-2 h-3.5 w-3.5 text-muted-foreground" />
                    {[1, 2, 3, 4].map((n) => (
                      <button
                        key={n}
                        onClick={() => setPax(n)}
                        className={cn(
                          "flex h-7 w-7 items-center justify-center rounded-md text-[12px] font-bold transition-all",
                          pax === n
                            ? "bg-card text-foreground shadow-sm"
                            : "text-muted-foreground hover:text-foreground"
                        )}
                      >
                        {n}
                      </button>
                    ))}
                  </div>
                </div>

                {/* CTA */}
                <div className="px-5 pb-5">
                  <button
                    onClick={() => setPhase("results")}
                    className="group flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-4 text-[15px] font-bold text-brand-foreground shadow-[var(--shadow-glow)] transition-all hover:bg-brand-strong hover:shadow-[0_8px_24px_var(--color-brand)/40] active:scale-[0.98]"
                  >
                    Compare Rides
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </button>
                </div>
              </Panel>

              {/* Quick routes */}
              <div className="mt-5 flex flex-wrap justify-center gap-2">
                {quickRoutes.map((r) => (
                  <button
                    key={r.label}
                    onClick={() => { setFrom(r.from); setTo(r.to); }}
                    className="rounded-full border border-border/60 bg-card/60 px-4 py-2 text-[12px] font-semibold text-muted-foreground backdrop-blur-sm transition-all hover:border-brand/30 hover:bg-brand-soft/30 hover:text-brand"
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* ═══ RESULTS STATE ═══ */}
        {phase === "results" && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="mx-auto max-w-2xl space-y-5 pb-16"
          >
            {/* Compact route pill */}
            <div className="sticky top-0 z-20 -mx-4 flex items-center justify-between gap-3 border-b border-border bg-background/90 px-4 py-3 backdrop-blur-xl sm:mx-0 sm:rounded-2xl sm:border sm:px-5">
              <div className="flex min-w-0 items-center gap-2 text-[13px] font-semibold">
                <div className="h-2 w-2 shrink-0 rounded-full bg-brand" />
                <span className="truncate">{from.split(",")[0]}</span>
                <ArrowRight className="h-3 w-3 shrink-0 text-muted-foreground" />
                <span className="truncate">{to || "BLR Airport"}</span>
                <span className="shrink-0 text-muted-foreground">·</span>
                <span className="shrink-0 text-muted-foreground">{when}</span>
                <span className="shrink-0 text-muted-foreground">·</span>
                <span className="shrink-0 text-muted-foreground">{pax} pax</span>
              </div>
              <button
                onClick={() => setPhase("input")}
                className="shrink-0 flex items-center gap-1.5 rounded-lg border border-border bg-surface-2/80 px-3 py-1.5 text-[12px] font-bold text-muted-foreground transition-all hover:border-brand/30 hover:text-brand"
              >
                <Edit2 className="h-3 w-3" /> Edit
              </button>
            </div>


            {/* ⚡ Surge alert banner */}
            <div className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900/40 dark:bg-amber-950/30">
              <Zap className="h-4 w-4 shrink-0 text-amber-600" />
              <p className="flex-1 text-[12px] font-semibold text-amber-800 dark:text-amber-200">
                <span className="font-bold">Uber surge active</span> right now — Ola is ₹43 cheaper on your route. Surge usually ends in ~8 min.
              </p>
              <Tag tone="warning" className="text-[10px] shrink-0">Live</Tag>
            </div>

            {/* NEXA Recommends banner */}
            <div className="overflow-hidden rounded-2xl border border-brand/20 bg-gradient-to-r from-brand-soft/40 via-brand-soft/20 to-transparent p-5">
              <div className="flex items-start gap-3">
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-brand/15">
                  <Sparkles className="h-4 w-4 text-brand" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-brand">
                      NEXA Recommends
                    </p>
                    <Tag tone="brand" className="text-[10px]">Score {recommended.score}</Tag>
                  </div>
                  <p className="mt-1 text-[16px] font-bold text-foreground">{recommended.name}</p>
                  {recommended.quote && (
                    <p className="mt-0.5 text-[13px] text-muted-foreground">{recommended.quote}</p>
                  )}
                </div>
                <button className="shrink-0 rounded-xl bg-brand px-4 py-2 text-[13px] font-bold text-brand-foreground shadow-[var(--shadow-glow)] transition-all hover:bg-brand-strong active:scale-95">
                  Book →
                </button>
              </div>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground/60">
                Sort:
              </span>
              {filters.map((f) => (
                <button
                  key={f}
                  onClick={() => setActiveFilter(f)}
                  className={cn(
                    "rounded-full border px-3.5 py-1.5 text-[12px] font-semibold transition-all",
                    activeFilter === f
                      ? "border-brand bg-brand-soft/40 text-brand"
                      : "border-border bg-card text-muted-foreground hover:border-brand/30 hover:text-foreground"
                  )}
                >
                  {f}
                </button>
              ))}
            </div>

            {/* Provider cards */}
            <Stagger className="space-y-3">
              {sorted.map((p) => (
                <StaggerItem key={p.id}>
                  <div
                    className={cn(
                      "group relative overflow-hidden rounded-2xl border bg-card transition-all hover:-translate-y-0.5 hover:shadow-md",
                      p.recommended
                        ? "border-brand/30 bg-brand-soft/10 shadow-[var(--elev-card)]"
                        : p.cheapest
                        ? "border-positive/20"
                        : "border-border hover:border-border/80"
                    )}
                  >
                    {/* Colored left accent bar */}
                    <div className={cn("absolute inset-y-0 left-0 w-1 rounded-l-2xl", p.accent.replace("border-l-", "bg-"))} />

                    <div className="flex items-center gap-4 px-5 py-4 pl-6">
                      {/* Provider logo */}
                      <div className={cn("grid h-10 w-10 shrink-0 place-items-center rounded-xl text-[15px] font-black shadow-sm", p.color)}>
                        {p.initial}
                      </div>

                      {/* Name + type + ETA */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[14px] font-bold">{p.name}</span>
                          <span className="rounded-md bg-surface-2 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                            {p.type}
                          </span>
                          {p.recommended && <Tag tone="brand" className="text-[10px]">NEXA PICK</Tag>}
                          {p.cheapest && <Tag tone="positive" className="text-[10px]">CHEAPEST</Tag>}
                        </div>
                        <div className="mt-1 flex items-center gap-3">
                          {/* ETA bar */}
                          <div className="flex items-center gap-1.5">
                            <Clock className="h-3 w-3 text-muted-foreground" />
                            <span className="text-[12px] font-medium text-muted-foreground">{p.eta} min ETA</span>
                          </div>
                          <div className="h-1 w-16 overflow-hidden rounded-full bg-surface-2">
                            <div
                              className="h-full rounded-full bg-brand/60"
                              style={{ width: `${Math.max(15, 100 - p.eta * 12)}%` }}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Price + book */}
                      <div className="flex shrink-0 items-center gap-4">
                        <div className="text-right">
                          <p className="tc-num text-[22px] font-bold leading-none">{inr(p.price)}</p>
                          <p className="mt-0.5 text-[10px] font-medium text-muted-foreground">
                            Score {p.score}
                          </p>
                        </div>
                        <button
                          className={cn(
                            "rounded-xl px-4 py-2 text-[13px] font-bold transition-all active:scale-95",
                            p.recommended
                              ? "bg-brand text-brand-foreground shadow-[var(--shadow-glow)] hover:bg-brand-strong"
                              : "border border-border bg-surface-2 text-foreground hover:border-brand/30 hover:bg-brand-soft/20 hover:text-brand"
                          )}
                        >
                          Book
                        </button>
                      </div>
                    </div>
                    {/* TrueCost breakdown */}
                    <div className="border-t border-border/50 px-6 pb-4 pt-3">
                      <TrueCostBar
                        base={Math.round(p.price * 0.82)}
                        fee={Math.round(p.price * 0.10)}
                        tax={p.price - Math.round(p.price * 0.82) - Math.round(p.price * 0.10)}
                        className="text-[10px]"
                      />
                    </div>
                  </div>
                </StaggerItem>
              ))}
            </Stagger>

            {/* Disclaimer */}
            <div className="flex items-center justify-center gap-1.5 text-[11px] text-muted-foreground/60">
              <Info className="h-3 w-3" />
              Prices are estimated. Final fare may vary with surge pricing.
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </AppShell>
  );
}
