import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  ArrowLeftRight,
  Bell,
  Calendar,
  Check,
  ChevronRight,
  Edit2,
  Plane,
  Sparkles,
  Users,
} from "lucide-react";
import { AppShell } from "@/components/tc/app-shell";
import { Panel, Tag, Stagger, StaggerItem } from "@/components/tc/ui-kit";
import { inr } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/travel")({
  head: () => ({
    meta: [{ title: "Flight Intelligence — TrueCost" }],
  }),
  component: TravelFlights,
});

/* ── Mock data ── */
const flights = [
  { id: "1", airline: "IndiGo",    code: "6E", flight: "6E-431", dep: "06:15", arr: "09:00", dur: "2h 45m", stops: "Non-stop", price: 4299, score: 93, color: "bg-indigo-600" },
  { id: "2", airline: "Air India", code: "AI", flight: "AI-130", dep: "07:00", arr: "09:45", dur: "2h 45m", stops: "Non-stop", price: 5199, score: 89, color: "bg-red-600" },
  { id: "3", airline: "Vistara",   code: "VS", flight: "UK-801", dep: "08:30", arr: "11:15", dur: "2h 45m", stops: "Non-stop", price: 5499, score: 87, color: "bg-purple-600" },
  { id: "4", airline: "SpiceJet",  code: "SJ", flight: "SG-123", dep: "11:30", arr: "14:15", dur: "2h 45m", stops: "Non-stop", price: 3899, score: 87, color: "bg-orange-500" },
  { id: "5", airline: "IndiGo",    code: "6E", flight: "6E-201", dep: "14:00", arr: "16:45", dur: "2h 45m", stops: "Non-stop", price: 3499, score: 84, color: "bg-indigo-600" },
  { id: "6", airline: "GoAir",     code: "G8", flight: "G8-401", dep: "16:30", arr: "19:45", dur: "3h 15m", stops: "1 stop",    price: 2999, score: 76, color: "bg-teal-600" },
];

const popularRoutes = ["BLR → DEL", "BLR → BOM", "BLR → GOI", "BLR → DXB", "BLR → HYD"];

function TravelFlights() {
  const [phase, setPhase] = useState<"input" | "results">("input");
  const [tripType, setTripType] = useState("One way");
  const [cabin, setCabin] = useState("Economy");
  const [fromCity, setFromCity] = useState("Bangalore");
  const [fromCode, setFromCode] = useState("BLR");
  const [toCity, setToCity] = useState("New Delhi");
  const [toCode, setToCode] = useState("DEL");

  const featuredPicks = [
    { badge: "BEST OVERALL", tone: "brand" as const,    accent: "bg-brand",   f: flights[0]! },
    { badge: "BEST PRICE",   tone: "positive" as const, accent: "bg-positive", f: flights[3]! },
    { badge: "BEST TIMING",  tone: "gold" as const,     accent: "bg-amber-400",f: flights[1]! },
  ];

  return (
    <AppShell>
      <AnimatePresence mode="wait">

        {/* ═══ INPUT — typographic hero ═══ */}
        {phase === "input" && (
          <motion.div
            key="input"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -16, scale: 0.98 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="flex min-h-[82vh] flex-col items-center justify-center px-4 py-12"
          >
            {/* Heading */}
            <div className="mb-10 text-center">
              <p className="mb-3 text-[11px] font-bold uppercase tracking-[0.18em] text-brand">
                Flight Intelligence
              </p>
              <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
                Find your perfect flight
              </h1>
              <p className="mt-3 text-[15px] text-muted-foreground">
                Compare all airlines — NEXA finds the real best price including fees & baggage
              </p>
            </div>

            {/* Search card */}
            <Panel elevation="raised" className="w-full max-w-3xl overflow-hidden">
              {/* Trip type row */}
              <div className="flex gap-1 border-b border-border/60 p-4">
                {["One way", "Round trip", "Multi-city"].map((t) => (
                  <button
                    key={t}
                    onClick={() => setTripType(t)}
                    className={cn(
                      "flex items-center gap-1.5 rounded-lg px-4 py-2 text-[13px] font-semibold transition-all",
                      tripType === t
                        ? "bg-brand text-brand-foreground"
                        : "text-muted-foreground hover:bg-surface-2 hover:text-foreground"
                    )}
                  >
                    {tripType === t && <Check className="h-3 w-3" />}
                    {t}
                  </button>
                ))}
              </div>

              <div className="p-5 space-y-4">
                {/* From → To — typographic, not form-like */}
                <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
                  <div className="rounded-2xl border border-border bg-surface-2/40 p-4 transition-all focus-within:border-brand/40">
                    <p className="mb-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-muted-foreground">From</p>
                    <p className="tc-num text-[32px] font-black leading-none text-foreground">
                      {fromCode}
                    </p>
                    <p className="mt-1 text-[13px] text-muted-foreground">{fromCity}</p>
                  </div>

                  <button
                    onClick={() => {
                      const [fc, cc, ft, ct] = [fromCity, fromCode, toCity, toCode];
                      setFromCity(ft); setFromCode(ct);
                      setToCity(fc); setToCode(cc);
                    }}
                    className="grid h-10 w-10 place-items-center rounded-full border border-border bg-card text-muted-foreground shadow-sm transition-all hover:border-brand/40 hover:text-brand active:scale-90"
                  >
                    <ArrowLeftRight className="h-4 w-4" />
                  </button>

                  <div className="rounded-2xl border border-border bg-surface-2/40 p-4 transition-all focus-within:border-brand/40">
                    <p className="mb-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-muted-foreground">To</p>
                    <p className="tc-num text-[32px] font-black leading-none text-foreground">
                      {toCode}
                    </p>
                    <p className="mt-1 text-[13px] text-muted-foreground">{toCity}</p>
                  </div>
                </div>

                {/* Dates + passengers */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="flex items-center gap-2 rounded-xl border border-border bg-surface-2/40 px-4 py-3">
                    <Calendar className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">Depart</p>
                      <p className="text-[13px] font-bold">24 May</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 rounded-xl border border-border bg-surface-2/40 px-4 py-3">
                    <Calendar className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">Return</p>
                      <p className="text-[13px] font-bold">31 May</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 rounded-xl border border-border bg-surface-2/40 px-4 py-3">
                    <Users className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">Passengers</p>
                      <p className="text-[13px] font-bold">1 Adult</p>
                    </div>
                  </div>
                </div>

                {/* Cabin class */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] font-semibold text-muted-foreground">Cabin:</span>
                  {["Economy", "Premium Economy", "Business", "First"].map((c) => (
                    <button
                      key={c}
                      onClick={() => setCabin(c)}
                      className={cn(
                        "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[12px] font-semibold transition-all",
                        cabin === c
                          ? "bg-brand text-brand-foreground shadow-[var(--shadow-glow)]"
                          : "border border-border text-muted-foreground hover:border-brand/30 hover:text-foreground"
                      )}
                    >
                      {cabin === c && <Check className="h-3 w-3" />} {c}
                    </button>
                  ))}
                </div>

                {/* Search CTA */}
                <button
                  onClick={() => setPhase("results")}
                  className="group flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-4 text-[15px] font-bold text-brand-foreground shadow-[var(--shadow-glow)] transition-all hover:bg-brand-strong hover:shadow-[0_8px_24px_var(--color-brand)/40] active:scale-[0.98]"
                >
                  <Plane className="h-4 w-4" />
                  Search & Compare Flights
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </button>
              </div>
            </Panel>

            {/* Popular routes */}
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              {popularRoutes.map((r) => (
                <button
                  key={r}
                  className="rounded-full border border-border/50 bg-card/60 px-4 py-2 text-[12px] font-semibold text-muted-foreground backdrop-blur-sm transition-all hover:border-brand/30 hover:bg-brand-soft/20 hover:text-brand"
                >
                  {r}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {/* ═══ RESULTS ═══ */}
        {phase === "results" && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
            className="mx-auto max-w-4xl space-y-6 pb-16"
          >
            {/* Sticky compact header */}
            <div className="sticky top-0 z-20 -mx-4 flex items-center justify-between gap-3 border-b border-border bg-background/90 px-4 py-3 backdrop-blur-xl sm:mx-0 sm:rounded-2xl sm:border sm:px-5">
              <div className="flex items-center gap-2 text-[13px] font-semibold">
                <span className="tc-num font-black">{fromCode}</span>
                <Plane className="h-3.5 w-3.5 text-brand" />
                <span className="tc-num font-black">{toCode}</span>
                <span className="text-muted-foreground">·</span>
                <span className="text-muted-foreground">24 May</span>
                <span className="text-muted-foreground">·</span>
                <span className="text-muted-foreground">1 Adult · {cabin}</span>
              </div>
              <button
                onClick={() => setPhase("input")}
                className="flex items-center gap-1.5 rounded-lg border border-border bg-surface-2/80 px-3 py-1.5 text-[12px] font-bold text-muted-foreground transition-all hover:border-brand/30 hover:text-brand"
              >
                <Edit2 className="h-3 w-3" /> Edit
              </button>
            </div>

            {/* 3 featured picks — boarding pass cards */}
            <Stagger className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {featuredPicks.map(({ badge, tone, accent, f }) => (
                <StaggerItem key={badge}>
                  <div className="relative overflow-hidden rounded-2xl border border-border bg-card transition-all hover:-translate-y-1 hover:shadow-lg cursor-pointer group">
                    {/* Top color accent */}
                    <div className={cn("h-1 w-full", accent)} />

                    <div className="p-5">
                      {/* Badge + airline */}
                      <div className="flex items-start justify-between">
                        <Tag tone={tone} className="text-[10px] font-bold">{badge}</Tag>
                        <div className={cn("grid h-8 w-8 place-items-center rounded-lg text-[11px] font-black text-white", f.color)}>
                          {f.code}
                        </div>
                      </div>

                      {/* Flight info */}
                      <div className="mt-4 space-y-1">
                        <p className="text-[13px] font-bold">{f.airline} <span className="font-normal text-muted-foreground">{f.flight}</span></p>
                        <div className="flex items-center gap-2">
                          <span className="tc-num text-[18px] font-black">{f.dep}</span>
                          <div className="flex flex-1 items-center gap-1">
                            <div className="h-px flex-1 border-t border-dashed border-border" />
                            <Plane className="h-3 w-3 text-muted-foreground" />
                            <div className="h-px flex-1 border-t border-dashed border-border" />
                          </div>
                          <span className="tc-num text-[18px] font-black">{f.arr}</span>
                        </div>
                        <div className="flex justify-between text-[11px] text-muted-foreground">
                          <span>{fromCode}</span>
                          <span>{f.dur} · {f.stops}</span>
                          <span>{toCode}</span>
                        </div>
                      </div>

                      {/* Divider (perforated) */}
                      <div className="my-4 border-t border-dashed border-border" />

                      {/* Price + select */}
                      <div className="flex items-end justify-between">
                        <div>
                          <p className="tc-num text-[22px] font-black leading-none">{inr(f.price)}</p>
                          <p className="mt-0.5 text-[10px] font-semibold text-brand">Score {f.score}</p>
                        </div>
                        <span className="flex items-center gap-1 text-[12px] font-bold text-brand transition-transform group-hover:translate-x-1">
                          Select <ChevronRight className="h-3.5 w-3.5" />
                        </span>
                      </div>
                    </div>
                  </div>
                </StaggerItem>
              ))}
            </Stagger>

            {/* NEXA insight */}
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="flex items-start gap-3 rounded-2xl border border-brand/20 bg-brand-soft/20 p-4"
            >
              <div className="grid h-7 w-7 shrink-0 place-items-center rounded-xl bg-brand/15">
                <Sparkles className="h-3.5 w-3.5 text-brand" />
              </div>
              <p className="text-[13px] leading-relaxed text-foreground/80">
                <strong className="font-bold text-foreground">IndiGo 6E-431</strong> is ₹400 more than
                the cheapest but has a 98% on-time rate on this route — best overall value for the price.
              </p>
            </motion.div>

            {/* All flights */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-[15px] font-bold">All Flights</h2>
                <p className="text-[12px] text-muted-foreground">Sorted by NEXA score</p>
              </div>

              <div className="space-y-2">
                {flights.map((f, i) => (
                  <motion.div
                    key={f.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.35 + i * 0.06 }}
                  >
                    <div className="group flex items-center justify-between gap-4 rounded-xl border border-border bg-card px-4 py-3.5 transition-all hover:border-brand/30 hover:bg-brand-soft/5 cursor-pointer">
                      <div className="flex items-center gap-3">
                        {/* Airline badge */}
                        <div className={cn("grid h-8 w-8 shrink-0 place-items-center rounded-lg text-[11px] font-black text-white", f.color)}>
                          {f.code}
                        </div>
                        <div>
                          <p className="text-[13px] font-bold">{f.airline} <span className="font-normal text-muted-foreground">{f.flight}</span></p>
                          <p className="text-[11px] text-muted-foreground">{f.stops}</p>
                        </div>
                      </div>

                      {/* Times */}
                      <div className="hidden items-center gap-2 sm:flex">
                        <span className="tc-num text-[14px] font-bold">{f.dep}</span>
                        <div className="flex items-center gap-1 text-muted-foreground">
                          <div className="h-px w-8 border-t border-dashed border-current" />
                          <span className="text-[10px]">{f.dur}</span>
                          <div className="h-px w-8 border-t border-dashed border-current" />
                        </div>
                        <span className="tc-num text-[14px] font-bold">{f.arr}</span>
                      </div>

                      {/* Price + score */}
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="tc-num text-[16px] font-bold">{inr(f.price)}</p>
                          <div className="flex items-center justify-end gap-1.5">
                            <div className="h-1 w-12 overflow-hidden rounded-full bg-surface-2">
                              <div className="h-full rounded-full bg-brand" style={{ width: `${f.score}%` }} />
                            </div>
                            <span className="text-[10px] font-semibold text-muted-foreground">{f.score}</span>
                          </div>
                        </div>
                        <button className="hidden rounded-lg border border-border px-3 py-1.5 text-[12px] font-bold transition-all group-hover:border-brand group-hover:bg-brand group-hover:text-brand-foreground sm:block">
                          Select
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Price alert CTA */}
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="group flex w-full items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-border p-6 text-center transition-all hover:border-brand/40 hover:bg-brand-soft/10"
            >
              <div className="grid h-9 w-9 place-items-center rounded-full bg-surface-2 transition-all group-hover:bg-brand-soft">
                <Bell className="h-4 w-4 text-muted-foreground group-hover:text-brand" />
              </div>
              <div className="text-left">
                <p className="text-[14px] font-bold">Set price alert for {fromCode} → {toCode}</p>
                <p className="text-[12px] text-muted-foreground">Notify me if prices drop below ₹3,499</p>
              </div>
            </motion.button>
          </motion.div>
        )}

      </AnimatePresence>
    </AppShell>
  );
}
