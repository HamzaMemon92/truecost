/**
 * Ask NEXA — Full-screen AI command center.
 * Sidebar auto-hides. History panel hidden on idle — pure hero layout.
 */
import { useState, useRef, useEffect, type KeyboardEvent } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowRight,
  ArrowUp,
  Car,
  Clock,
  History,
  Laptop,
  Leaf,
  MapPin,
  Mic,
  Paperclip,
  Plane,
  ShoppingBasket,
  Sparkles,
  Star,
  UtensilsCrossed,
  X,
} from "lucide-react";
import { AppShell } from "@/components/tc/app-shell";
import { Tag, NexaSearching } from "@/components/tc/ui-kit";
import { BrandLogo } from "@/components/tc/brand-logo";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/ask")({
  head: () => ({
    meta: [
      { title: "Ask NEXA — TrueCost" },
      {
        name: "description",
        content:
          "Ask your AI consumer agent anything. Compare, decide and buy smarter with NEXA.",
      },
    ],
  }),
  component: AskNexa,
});

/* ─── Suggestion chips ─── */
const suggestions = [
  { label: "Find me a ride to the airport", icon: Car },
  { label: "Best laptop under ₹80,000", icon: Laptop },
  { label: "Cheapest grocery basket", icon: ShoppingBasket },
  { label: "Flights to Goa this weekend", icon: Plane },
  { label: "Compare food delivery prices", icon: UtensilsCrossed },
];

/* ─── Mock recent conversations ─── */
const recents = [
  { id: 1, title: "Best laptop for AI development", time: "2h ago", icon: Laptop },
  { id: 2, title: "Ride to BLR Airport", time: "Yesterday", icon: Car },
  { id: 3, title: "Weekly grocery basket comparison", time: "2 days ago", icon: ShoppingBasket },
  { id: 4, title: "Dubai flights for June 12", time: "Last week", icon: Plane },
];

/* ─── Mock result cards ─── */
const resultCards = [
  {
    badge: "Best Overall",
    badgeTone: "brand" as const,
    name: "MacBook Air M3 13\"",
    price: 79990,
    score: 94,
    seller: "Amazon",
    tagTone: "gold" as const,
    tag: "★ Recommended",
    specs: "Apple M3 · 8GB · 512GB SSD",
  },
  {
    badge: "Best Value",
    badgeTone: "positive" as const,
    name: "ASUS ROG Zephyrus G14",
    price: 72499,
    score: 89,
    seller: "Flipkart",
    tagTone: "info" as const,
    tag: "Top pick",
    specs: "Ryzen 9 · 16GB · 1TB SSD",
  },
  {
    badge: "Best Budget",
    badgeTone: "neutral" as const,
    name: "Lenovo IdeaPad Slim 5",
    price: 54999,
    score: 82,
    seller: "Amazon",
    tagTone: "neutral" as const,
    tag: "Great value",
    specs: "Ryzen 5 · 16GB · 512GB SSD",
  },
];

const searchSteps = [
  "Understanding your request",
  "Finding relevant products",
  "Comparing prices across sellers",
  "Checking trust signals",
  "Calculating your best option",
];

type Phase = "idle" | "searching" | "results";

function AskNexa() {
  const [query, setQuery] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [searchStep, setSearchStep] = useState(0);
  const [historyOpen, setHistoryOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = () => {
    if (!query.trim()) return;
    setPhase("searching");
    setSearchStep(0);
    let step = 0;
    const interval = setInterval(() => {
      step++;
      setSearchStep(step);
      if (step >= searchSteps.length) {
        clearInterval(interval);
        setTimeout(() => setPhase("results"), 300);
      }
    }, 420);
  };

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") handleSubmit();
  };

  return (
    <AppShell>
      {/* Break out of AppShell padding to go full-bleed */}
      <div className="-mt-5 -mx-4 sm:-mx-6 flex min-h-[calc(100vh-56px)] overflow-hidden relative">

        {/* ── History drawer (slide in from left, overlay) ── */}
        <AnimatePresence>
          {historyOpen && (
            <>
              <motion.div
                key="history-backdrop"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setHistoryOpen(false)}
                className="fixed inset-0 z-40 bg-foreground/20 backdrop-blur-sm"
              />
              <motion.aside
                key="history-panel"
                initial={{ x: -260 }}
                animate={{ x: 0 }}
                exit={{ x: -260 }}
                transition={{ type: "spring", stiffness: 380, damping: 36 }}
                className="fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-border bg-card shadow-[var(--elev-floating)]"
              >
                <div className="flex items-center justify-between border-b border-border px-4 py-3.5">
                  <p className="text-[12px] font-bold uppercase tracking-wider text-muted-foreground">
                    History
                  </p>
                  <button
                    onClick={() => setHistoryOpen(false)}
                    className="rounded-md p-1 text-muted-foreground hover:bg-muted"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto p-2">
                  <p className="flex items-center gap-1 px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60">
                    <Clock className="h-3 w-3" /> Recent
                  </p>
                  {recents.map((r) => (
                    <button
                      key={r.id}
                      className="group flex w-full items-start gap-2.5 rounded-xl px-2.5 py-2.5 text-left transition-colors hover:bg-surface-2"
                    >
                      <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-muted text-muted-foreground transition-colors group-hover:bg-brand-soft group-hover:text-brand">
                        <r.icon className="h-3.5 w-3.5" />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-[12px] font-medium leading-tight text-foreground">
                          {r.title}
                        </span>
                        <span className="mt-0.5 block text-[10px] text-muted-foreground">
                          {r.time}
                        </span>
                      </span>
                    </button>
                  ))}
                </div>
                <div className="border-t border-border p-2">
                  <button className="w-full rounded-xl border border-dashed border-border px-3 py-2 text-[12px] font-medium text-muted-foreground transition-all hover:border-brand/30 hover:bg-brand-soft/30 hover:text-brand">
                    + New conversation
                  </button>
                </div>
              </motion.aside>
            </>
          )}
        </AnimatePresence>

        {/* ── Main area ── */}
        <div className="flex flex-1 flex-col">
          <AnimatePresence mode="wait">

            {/* ════════ IDLE: Pure centered hero ════════ */}
            {phase === "idle" && (
              <motion.div
                key="hero"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, y: -16 }}
                transition={{ duration: 0.3 }}
                className="flex flex-1 flex-col items-center justify-center px-6 py-20 relative"
              >
                {/* Ambient gradient blobs */}
                <div className="pointer-events-none absolute inset-0 overflow-hidden">
                  <div className="absolute left-1/2 top-[20%] h-72 w-[500px] -translate-x-1/2 rounded-full bg-brand/6 blur-[90px]" />
                  <div className="absolute left-[30%] top-[35%] h-48 w-48 rounded-full bg-violet-400/8 blur-[70px]" />
                  <div className="absolute right-[25%] top-[25%] h-40 w-40 rounded-full bg-sky-300/6 blur-[60px]" />
                </div>

                {/* History toggle button — top-left */}
                <button
                  onClick={() => setHistoryOpen(true)}
                  className="absolute left-4 top-4 flex items-center gap-1.5 rounded-xl border border-border bg-card/80 px-3 py-2 text-[12px] font-medium text-muted-foreground shadow-sm backdrop-blur-sm transition-all hover:border-brand/30 hover:text-brand"
                >
                  <History className="h-3.5 w-3.5" />
                  <span className="hidden sm:block">History</span>
                </button>

                {/* ── Headline ── */}
                <motion.div
                  initial={{ opacity: 0, y: 28 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05, duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
                  className="relative text-center"
                >
                  <p className="mb-5 text-[11px] font-bold uppercase tracking-[0.22em] text-muted-foreground">
                    The AI that works for you
                  </p>
                  <h1 className="tc-display max-w-3xl text-[52px] font-bold leading-[1.06] tracking-[-0.04em] text-foreground sm:text-[68px] lg:text-[76px]">
                    Before you spend,
                    <br />
                    <span className="text-brand">ask NEXA.</span>
                  </h1>
                  <p className="mx-auto mt-5 max-w-lg text-[15px] leading-relaxed text-muted-foreground sm:text-[16px]">
                    One intelligent agent for comparing, choosing and eventually
                    completing the things you buy, book and use.
                  </p>
                </motion.div>

                {/* ── Big input box ── */}
                <motion.div
                  initial={{ opacity: 0, y: 28 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.18, duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
                  className="relative mt-12 w-full max-w-2xl"
                >
                  <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-[0_8px_40px_rgba(0,0,0,0.09)] transition-all focus-within:border-brand/35 focus-within:shadow-[0_12px_48px_rgba(var(--color-brand)/0.11)]">
                    {/* Main input row */}
                    <div className="flex items-center gap-3 px-5 py-4 sm:py-5">
                      <Sparkles className="h-5 w-5 shrink-0 text-brand" />
                      <input
                        ref={inputRef}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={handleKey}
                        placeholder="Find the best flight to Toronto…"
                        className="min-w-0 flex-1 bg-transparent text-[16px] font-medium text-foreground placeholder:text-muted-foreground/55 focus:outline-none sm:text-[17px]"
                      />
                      <motion.button
                        whileTap={{ scale: 0.9 }}
                        onClick={handleSubmit}
                        disabled={!query.trim()}
                        className={cn(
                          "grid h-10 w-10 shrink-0 place-items-center rounded-xl transition-all",
                          query.trim()
                            ? "bg-brand text-brand-foreground shadow-[var(--shadow-glow)] hover:scale-105 hover:bg-brand-strong"
                            : "bg-muted text-muted-foreground/40 cursor-not-allowed"
                        )}
                      >
                        <ArrowUp className="h-5 w-5" />
                      </motion.button>
                    </div>

                    {/* Bottom row */}
                    <div className="flex items-center justify-between border-t border-border/50 bg-surface-2/50 px-5 py-2.5">
                      <div className="flex items-center gap-4 text-muted-foreground">
                        <button
                          className="transition-colors hover:text-foreground"
                          title="Voice input"
                        >
                          <Mic className="h-4 w-4" />
                        </button>
                        <button
                          className="transition-colors hover:text-foreground"
                          title="Attach file"
                        >
                          <Paperclip className="h-4 w-4" />
                        </button>
                        <div className="flex items-center gap-1.5 text-[11px]">
                          <MapPin className="h-3 w-3" />
                          <span>Powai, Mumbai</span>
                        </div>
                      </div>
                      <p className="text-[11px] text-muted-foreground/55">
                        Demo data · nothing is purchased
                      </p>
                    </div>
                  </div>
                </motion.div>

                {/* ── Suggestion chips ── */}
                <motion.div
                  initial={{ opacity: 0, y: 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                  className="mt-5 flex flex-wrap items-center justify-center gap-2"
                >
                  {suggestions.map((s) => (
                    <button
                      key={s.label}
                      onClick={() => {
                        setQuery(s.label);
                        inputRef.current?.focus();
                      }}
                      className="flex items-center gap-1.5 rounded-full border border-border bg-card px-3.5 py-1.5 text-[12px] font-medium text-foreground/75 transition-all hover:-translate-y-0.5 hover:border-brand/25 hover:bg-brand-soft/40 hover:text-brand hover:shadow-sm"
                    >
                      <s.icon className="h-3 w-3" />
                      {s.label}
                    </button>
                  ))}
                </motion.div>

                {/* ── Social proof ── */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.45 }}
                  className="mt-10 flex items-center gap-2 text-[12px] text-muted-foreground"
                >
                  <div className="flex -space-x-1.5">
                    {["AM", "PK", "SR", "NR"].map((i) => (
                      <span
                        key={i}
                        className="grid h-6 w-6 place-items-center rounded-full border-2 border-background bg-gradient-to-br from-brand to-violet-500 text-[8px] font-bold text-white"
                      >
                        {i}
                      </span>
                    ))}
                  </div>
                  <span>42,000+ decisions made smarter this month</span>
                  <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                  <span className="font-semibold text-foreground">4.9</span>
                </motion.div>
              </motion.div>
            )}

            {/* ════════ SEARCHING ════════ */}
            {phase === "searching" && (
              <motion.div
                key="searching"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="flex flex-1 flex-col items-center justify-center px-4 py-16"
              >
                <div className="mb-8 w-full max-w-2xl">
                  <div className="ml-auto w-fit max-w-[80%] rounded-2xl rounded-tr-sm bg-brand-soft px-4 py-3">
                    <p className="text-[14px] font-medium text-brand-strong">{query}</p>
                  </div>
                </div>
                <div className="w-full max-w-sm">
                  <NexaSearching steps={searchSteps} currentStep={searchStep} />
                </div>
              </motion.div>
            )}

            {/* ════════ RESULTS: 3-panel layout ════════ */}
            {phase === "results" && (
              <motion.div
                key="results"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-1 overflow-hidden"
              >
                {/* History panel (desktop) */}
                <aside className="hidden w-56 shrink-0 flex-col border-r border-border xl:flex">
                  <div className="flex items-center justify-between border-b border-border px-4 py-3.5">
                    <p className="text-[12px] font-bold uppercase tracking-wider text-muted-foreground">
                      History
                    </p>
                    <button className="rounded-md p-1 text-muted-foreground hover:bg-muted">
                      <Sparkles className="h-3.5 w-3.5" />
                    </button>
                  </div>
                  <div className="flex-1 overflow-y-auto p-2">
                    {recents.map((r) => (
                      <button
                        key={r.id}
                        className="group flex w-full items-start gap-2.5 rounded-xl px-2.5 py-2.5 text-left transition-colors hover:bg-surface-2"
                      >
                        <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-muted text-muted-foreground transition-colors group-hover:bg-brand-soft group-hover:text-brand">
                          <r.icon className="h-3.5 w-3.5" />
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-[12px] font-medium leading-tight text-foreground">
                            {r.title}
                          </span>
                          <span className="mt-0.5 block text-[10px] text-muted-foreground">
                            {r.time}
                          </span>
                        </span>
                      </button>
                    ))}
                  </div>
                  <div className="border-t border-border p-2">
                    <button className="w-full rounded-xl border border-dashed border-border px-3 py-2 text-[12px] font-medium text-muted-foreground transition-all hover:border-brand/30 hover:bg-brand-soft/30 hover:text-brand">
                      + New conversation
                    </button>
                  </div>
                </aside>

                {/* Chat thread */}
                <div className="flex flex-1 flex-col overflow-hidden">
                  <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8">
                    {/* User query echo */}
                    <div className="mb-6 flex justify-end">
                      <div className="max-w-[70%] rounded-2xl rounded-tr-sm bg-brand-soft px-4 py-3">
                        <p className="text-[14px] font-medium text-brand-strong">{query}</p>
                      </div>
                    </div>

                    {/* NEXA response */}
                    <div className="flex items-start gap-3">
                      <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-brand text-brand-foreground shadow-[var(--shadow-glow)]">
                        <Sparkles className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="mb-4 text-[13px] text-muted-foreground">
                          I found{" "}
                          <span className="font-bold text-foreground">14 laptops</span>{" "}
                          matching your requirements. Here's my analysis:
                        </p>

                        {/* Result cards */}
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                          {resultCards.map((card, i) => (
                            <motion.div
                              key={card.name}
                              initial={{ opacity: 0, y: 12 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: i * 0.1, duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                              className="group relative overflow-hidden rounded-xl border border-border bg-card p-4 shadow-[var(--elev-card)] transition-all hover:-translate-y-0.5 hover:border-brand/20 hover:shadow-[var(--elev-raised)]"
                            >
                              {i === 0 && (
                                <span
                                  aria-hidden
                                  className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand to-transparent"
                                />
                              )}
                              <div className="mb-3 flex items-start justify-between gap-2">
                                <Tag tone={card.badgeTone}>{card.badge}</Tag>
                                <div className="flex flex-col items-center">
                                  <span className="tc-num text-[18px] font-bold leading-none text-brand">
                                    {card.score}
                                  </span>
                                  <span className="text-[9px] font-semibold text-muted-foreground">
                                    Score
                                  </span>
                                </div>
                              </div>
                              <p className="text-[13px] font-bold leading-tight text-foreground">
                                {card.name}
                              </p>
                              <p className="mt-0.5 text-[10px] text-muted-foreground">
                                {card.specs}
                              </p>
                              <div className="mt-3 flex items-center justify-between">
                                <div>
                                  <p className="tc-num text-[15px] font-bold text-foreground">
                                    ₹{card.price.toLocaleString("en-IN")}
                                  </p>
                                  <div className="mt-0.5 flex items-center gap-1">
                                    <BrandLogo name={card.seller} size={12} />
                                    <span className="text-[10px] text-muted-foreground">
                                      {card.seller}
                                    </span>
                                  </div>
                                </div>
                                <Tag tone={card.tagTone} className="text-[10px]">
                                  {card.tag}
                                </Tag>
                              </div>
                              <button className="mt-3 w-full rounded-lg bg-brand px-3 py-1.5 text-[12px] font-semibold text-brand-foreground transition-all hover:bg-brand-strong">
                                View details
                              </button>
                            </motion.div>
                          ))}
                        </div>

                        <motion.p
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.5 }}
                          className="mt-5 max-w-xl text-[13px] leading-relaxed text-muted-foreground"
                        >
                          The{" "}
                          <span className="font-semibold text-foreground">
                            MacBook Air M3
                          </span>{" "}
                          offers the best balance of performance, battery life and resale
                          value for AI workloads. Shall I compare these in detail?
                        </motion.p>

                        <motion.div
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.65 }}
                          className="mt-4 flex flex-wrap gap-2"
                        >
                          {["Compare these 3", "Show more options", "Filter by brand", "Set price alert"].map(
                            (chip) => (
                              <button
                                key={chip}
                                className="flex items-center gap-1.5 rounded-full border border-border bg-surface-2/60 px-3 py-1.5 text-[12px] font-medium text-foreground/80 transition-all hover:border-brand/30 hover:bg-brand-soft/40 hover:text-brand"
                              >
                                {chip}
                                <ArrowRight className="h-3 w-3" />
                              </button>
                            )
                          )}
                        </motion.div>
                      </div>
                    </div>
                  </div>

                  {/* Fixed bottom input */}
                  <div className="border-t border-border px-4 py-3 sm:px-8">
                    <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition-all focus-within:border-brand/40">
                      <div className="flex items-center gap-3 px-5 py-3">
                        <Sparkles className="h-4 w-4 shrink-0 text-brand" />
                        <input
                          placeholder="Ask a follow-up…"
                          className="min-w-0 flex-1 bg-transparent text-[14px] font-medium text-foreground placeholder:text-muted-foreground/60 focus:outline-none"
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              setQuery("");
                              setPhase("idle");
                            }
                          }}
                        />
                        <button
                          onClick={() => { setQuery(""); setPhase("idle"); }}
                          className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-brand text-brand-foreground hover:bg-brand-strong transition-colors"
                        >
                          <ArrowUp className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Context panel (desktop right) */}
                <motion.aside
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="hidden w-64 shrink-0 flex-col border-l border-border xl:flex"
                >
                  <div className="border-b border-border px-4 py-3.5">
                    <p className="text-[12px] font-bold uppercase tracking-wider text-muted-foreground">
                      Context
                    </p>
                  </div>
                  <div className="flex-1 space-y-4 overflow-y-auto p-4">
                    <div>
                      <p className="mb-2 text-[11px] font-semibold text-muted-foreground">
                        Active context
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {["Budget: ₹80,000", "Laptops", "AI Dev"].map((f) => (
                          <span
                            key={f}
                            className="flex items-center gap-1 rounded-md border border-brand/20 bg-brand-soft px-2 py-0.5 text-[11px] font-medium text-brand"
                          >
                            {f}{" "}
                            <button className="text-brand/60 hover:text-brand">×</button>
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="h-px bg-border" />

                    {/* Top result */}
                    <div className="rounded-xl border border-brand/20 bg-brand-soft/30 p-3">
                      <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-brand">
                        Top Result
                      </p>
                      <p className="text-[13px] font-bold leading-tight text-foreground">
                        MacBook Air M3 13"
                      </p>
                      <p className="mt-0.5 text-[10px] text-muted-foreground">
                        Apple M3 · 8GB · 512GB SSD
                      </p>
                      <div className="mt-2 flex items-center justify-between">
                        <p className="tc-num text-[15px] font-bold text-brand">₹79,990</p>
                        <div className="flex flex-col items-center">
                          <span className="tc-num text-[18px] font-bold text-positive">94</span>
                          <span className="text-[9px] text-muted-foreground">Score</span>
                        </div>
                      </div>
                      <Tag tone="positive" className="mt-1.5 text-[10px]">
                        Best for you
                      </Tag>
                      <div className="mt-2.5 flex gap-1.5">
                        <button className="flex-1 rounded-lg bg-brand py-1.5 text-[11px] font-semibold text-brand-foreground hover:bg-brand-strong transition-colors">
                          Compare
                        </button>
                        <button className="flex-1 rounded-lg border border-border py-1.5 text-[11px] font-medium text-foreground hover:bg-muted transition-colors">
                          Watch
                        </button>
                      </div>
                    </div>

                    <div className="h-px bg-border" />

                    {/* Agent activity */}
                    <div>
                      <p className="mb-2.5 text-[11px] font-semibold text-muted-foreground">
                        Agent Activity
                      </p>
                      {[
                        { icon: "🔍", name: "Search Agent", detail: "Scanned 14 products" },
                        { icon: "💰", name: "Price Agent", detail: "Checked 6 sellers" },
                        { icon: "🛡️", name: "Trust Agent", detail: "Verified 14 sellers" },
                        { icon: "⭐", name: "Review Agent", detail: "Analyzed 2,847 reviews" },
                      ].map((a, i) => (
                        <motion.div
                          key={a.name}
                          initial={{ opacity: 0, x: 8 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.12 + 0.3 }}
                          className="flex items-center gap-2.5 py-1.5"
                        >
                          <span className="text-sm">{a.icon}</span>
                          <div className="min-w-0 flex-1">
                            <p className="text-[11px] font-semibold text-foreground">{a.name}</p>
                            <p className="text-[10px] text-muted-foreground">{a.detail}</p>
                          </div>
                          <motion.span
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ delay: i * 0.12 + 0.7, type: "spring" }}
                            className="grid h-4 w-4 shrink-0 place-items-center rounded-full bg-positive text-[9px] font-bold text-white"
                          >
                            ✓
                          </motion.span>
                        </motion.div>
                      ))}
                    </div>

                    {/* Sustainability nudge */}
                    <div className="rounded-xl border border-positive/20 bg-positive-soft/30 p-3">
                      <div className="flex items-center gap-1.5 text-positive">
                        <Leaf className="h-3.5 w-3.5" />
                        <p className="text-[11px] font-semibold">CO₂ impact</p>
                      </div>
                      <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
                        MacBook Air has{" "}
                        <span className="font-semibold text-foreground">18% lower</span>{" "}
                        lifecycle carbon footprint vs comparable Windows laptops.
                      </p>
                    </div>
                  </div>
                </motion.aside>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </AppShell>
  );
}
