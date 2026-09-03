/**
 * TrueCost Command Bar — ⌘+K global intent palette.
 *
 * Opens as a full-screen overlay. Detects category intent from input,
 * shows recent searches, and routes user to the right workspace.
 */
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowRight,
  Car,
  Clock,
  Hotel,
  Laptop,
  Plane,
  Search,
  ShoppingBasket,
  Sparkles,
  TrendingUp,
  UtensilsCrossed,
  X,
  Zap,
} from "lucide-react";
import { useRouter } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

/* ─── Intent detection ─── */
const intentRules: { pattern: RegExp; label: string; icon: typeof Car; route: string; color: string }[] = [
  { pattern: /ride|auto|cab|taxi|uber|ola|airport|pick.?up/i, label: "Rides", icon: Car, route: "/compare/rides", color: "bg-blue-100 text-blue-600" },
  { pattern: /grocery|milk|eggs|vegetables|blinkit|zepto|instamart/i, label: "Grocery", icon: ShoppingBasket, route: "/grocery", color: "bg-green-100 text-green-600" },
  { pattern: /food|pizza|burger|restaurant|swiggy|zomato|eat|hungry|craving/i, label: "Food", icon: UtensilsCrossed, route: "/food", color: "bg-orange-100 text-orange-600" },
  { pattern: /flight|fly|airline|indigo|airindia|depart|travel to/i, label: "Flights", icon: Plane, route: "/travel", color: "bg-sky-100 text-sky-600" },
  { pattern: /hotel|stay|check.?in|resort|book a room/i, label: "Hotels", icon: Hotel, route: "/hotels", color: "bg-violet-100 text-violet-600" },
  { pattern: /laptop|phone|iphone|samsung|headphone|tv|appliance|buy|product/i, label: "Products", icon: Laptop, route: "/compare/product", color: "bg-purple-100 text-purple-600" },
];

const recent = [
  { text: "Ride to BLR Airport", route: "/compare/rides", icon: Car },
  { text: "Weekly grocery basket", route: "/grocery", icon: ShoppingBasket },
  { text: "MacBook Air M3", route: "/compare/product", icon: Laptop },
  { text: "Goa flights this weekend", route: "/travel", icon: Plane },
];

const suggestions = [
  { text: "Find me a ride to the airport", icon: Car },
  { text: "Compare my grocery basket", icon: ShoppingBasket },
  { text: "Best laptop under ₹80,000", icon: Laptop },
  { text: "Book a hotel in Mumbai", icon: Hotel },
  { text: "Flights to Delhi next Friday", icon: Plane },
  { text: "Order food near me", icon: UtensilsCrossed },
];

function detectIntent(q: string) {
  for (const rule of intentRules) {
    if (rule.pattern.test(q)) return rule;
  }
  return null;
}

/* ─── CommandBar component ─── */
export function CommandBar() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const intent = query.trim().length > 2 ? detectIntent(query) : null;

  // ⌘+K / Ctrl+K listener
  useEffect(() => {
    const handler = (e: globalThis.KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 80);
    else setQuery("");
  }, [open]);

  const navigate = (route: string) => {
    router.navigate({ to: route as never });
    setOpen(false);
  };

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && intent) navigate(intent.route);
    if (e.key === "Enter" && !intent && query.trim()) navigate("/ask");
  };

  return (
    <>
      {/* Trigger button (in top bar) */}
      <button
        onClick={() => setOpen(true)}
        className="hidden sm:flex items-center gap-2.5 rounded-xl border border-border bg-surface-2/80 px-3.5 py-2 text-[13px] text-muted-foreground transition-all hover:border-brand/30 hover:bg-brand-soft/30 hover:text-foreground"
        aria-label="Open command bar (Ctrl+K)"
      >
        <Search className="h-3.5 w-3.5" />
        <span>Ask your agent anything…</span>
        <kbd className="ml-2 flex items-center gap-0.5 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium">
          <span>⌘</span><span>K</span>
        </kbd>
      </button>

      {/* Overlay */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[100] flex items-start justify-center bg-black/40 backdrop-blur-sm pt-[12vh] px-4"
            onClick={(e) => { if (e.target === e.currentTarget) setOpen(false); }}
          >
            <motion.div
              initial={{ opacity: 0, y: -12, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.97 }}
              transition={{ type: "spring", stiffness: 420, damping: 36 }}
              className="w-full max-w-2xl overflow-hidden rounded-2xl border border-border bg-card shadow-[0_32px_64px_rgba(0,0,0,0.22)]"
            >
              {/* Input row */}
              <div className="flex items-center gap-3 border-b border-border px-4 py-3.5">
                <Sparkles className="h-5 w-5 shrink-0 text-brand" />
                <input
                  ref={inputRef}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKey}
                  placeholder="What do you need? (rides, groceries, flights, products…)"
                  className="flex-1 bg-transparent text-[15px] font-medium text-foreground placeholder:text-muted-foreground outline-none"
                />
                {query && (
                  <button onClick={() => setQuery("")} className="shrink-0 rounded-md p-1 text-muted-foreground hover:bg-muted">
                    <X className="h-4 w-4" />
                  </button>
                )}
                <button onClick={() => setOpen(false)} className="shrink-0 rounded-md border border-border px-2 py-1 text-[11px] text-muted-foreground hover:bg-muted">
                  ESC
                </button>
              </div>

              {/* Intent detection banner */}
              <AnimatePresence>
                {intent && (
                  <motion.button
                    key="intent"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    onClick={() => navigate(intent.route)}
                    className="flex w-full items-center gap-3 border-b border-border bg-brand-soft/40 px-4 py-3 text-left transition-colors hover:bg-brand-soft/60"
                  >
                    <span className={cn("grid h-8 w-8 place-items-center rounded-lg text-sm", intent.color)}>
                      <intent.icon className="h-4 w-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-[13px] font-semibold text-foreground">
                        Open <span className="text-brand">{intent.label}</span> workspace
                      </p>
                      <p className="text-[11px] text-muted-foreground">Press ↵ to go</p>
                    </div>
                    <Zap className="h-4 w-4 text-brand" />
                  </motion.button>
                )}
              </AnimatePresence>

              {/* Body */}
              <div className="max-h-[380px] overflow-y-auto p-3">
                {query.trim().length === 0 ? (
                  <>
                    {/* Recent */}
                    <p className="mb-2 flex items-center gap-1.5 px-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                      <Clock className="h-3 w-3" /> Recent
                    </p>
                    {recent.map((r) => (
                      <button
                        key={r.text}
                        onClick={() => navigate(r.route)}
                        className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors hover:bg-surface-2"
                      >
                        <span className="grid h-7 w-7 place-items-center rounded-lg bg-muted text-muted-foreground">
                          <r.icon className="h-3.5 w-3.5" />
                        </span>
                        <span className="text-[13px] font-medium text-foreground">{r.text}</span>
                        <ArrowRight className="ml-auto h-3.5 w-3.5 text-muted-foreground" />
                      </button>
                    ))}

                    <div className="my-2 h-px bg-border" />

                    {/* Suggestions */}
                    <p className="mb-2 flex items-center gap-1.5 px-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                      <TrendingUp className="h-3 w-3" /> Try asking
                    </p>
                    {suggestions.map((s) => (
                      <button
                        key={s.text}
                        onClick={() => { setQuery(s.text); inputRef.current?.focus(); }}
                        className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left transition-colors hover:bg-surface-2"
                      >
                        <span className="grid h-7 w-7 place-items-center rounded-lg bg-brand-soft text-brand">
                          <s.icon className="h-3.5 w-3.5" />
                        </span>
                        <span className="text-[13px] text-muted-foreground">{s.text}</span>
                      </button>
                    ))}
                  </>
                ) : (
                  <>
                    {/* Search result: go to Ask NEXA */}
                    <button
                      onClick={() => navigate("/ask")}
                      className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition-colors hover:bg-surface-2"
                    >
                      <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand text-brand-foreground">
                        <Sparkles className="h-4 w-4" />
                      </span>
                      <div>
                        <p className="text-[13px] font-semibold">Ask NEXA: <span className="text-brand">"{query}"</span></p>
                        <p className="text-[11px] text-muted-foreground">Get AI-powered results and comparison</p>
                      </div>
                      <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
                    </button>

                    {/* Category shortcuts */}
                    <div className="mt-2">
                      <p className="mb-2 px-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Or search in</p>
                      <div className="grid grid-cols-3 gap-1.5">
                        {intentRules.map((r) => (
                          <button
                            key={r.label}
                            onClick={() => navigate(r.route)}
                            className={cn("flex items-center gap-2 rounded-xl px-3 py-2 text-left transition-all hover:scale-[1.02]", r.color)}
                          >
                            <r.icon className="h-3.5 w-3.5" />
                            <span className="text-[12px] font-semibold">{r.label}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between border-t border-border bg-surface-2/40 px-4 py-2">
                <p className="text-[11px] text-muted-foreground">
                  <kbd className="rounded border border-border bg-muted px-1.5 py-0.5 text-[10px]">↵</kbd>{" "}
                  to open workspace
                </p>
                <p className="text-[11px] text-muted-foreground">
                  <kbd className="rounded border border-border bg-muted px-1.5 py-0.5 text-[10px]">ESC</kbd>{" "}
                  to close
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
