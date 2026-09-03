import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import {
  Search,
  ArrowRight,
  ShoppingBag,
  Sparkles,
  Package,
  Truck,
  Edit2,
  Check,
  TrendingDown,
  Tag as TagIcon,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { AppShell } from "@/components/tc/app-shell";
import { Tag, Stagger, StaggerItem } from "@/components/tc/ui-kit";
import { inr } from "@/lib/mock-data";
import { executeShoppingWorkflow, type ShoppingProviderResult, type ShoppingWorkflowResult } from "@/lib/common-master/shopping-workflow";

export const Route = createFileRoute("/shopping")({
  head: () => ({
    meta: [
      { title: "Shopping TrueCost Compare | Veriq" },
      {
        name: "description",
        content:
          "Compare Amazon, Flipkart, Croma and Meesho on fee-inclusive TrueCost, delivery speed and seller trust before you buy.",
      },
      { property: "og:title", content: "Shopping TrueCost Compare | Veriq" },
      {
        property: "og:description",
        content: "See the real all-in price across every major retailer before you spend.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ShoppingRoute,
});

const popularSearches = [
  "iPhone 17 Pro",
  "OnePlus 13",
  "Sony WH-1000XM5",
  "Samsung 55\" TV",
  "MacBook Air M3",
];

const mockResults: ShoppingProviderResult[] = [
  {
    platform: "Amazon",
    mrp: 29990,
    price: 24990,
    delivery: 0,
    platformFee: 0,
    total: 24990,
    ships: "2 days",
    score: 91,
    isNexa: false,
    bgHeader: "from-orange-100 to-amber-100",
    accentText: "text-orange-700",
    title: "Sony WH-1000XM5 Wireless Headphones",
    brand: "Sony",
    trustSignal: "Verified seller",
  },
  {
    platform: "Flipkart",
    mrp: 29990,
    price: 24490,
    delivery: 0,
    platformFee: 0,
    total: 24490,
    ships: "1 day",
    score: 94,
    isNexa: true,
    bgHeader: "from-blue-100 to-indigo-100",
    accentText: "text-blue-700",
    title: "Sony WH-1000XM5 Wireless Headphones",
    brand: "Sony",
    trustSignal: "NEXA PICK",
  },
  {
    platform: "Meesho",
    mrp: 29990,
    price: 25990,
    delivery: 0,
    platformFee: 0,
    total: 25990,
    ships: "5 days",
    score: 78,
    isNexa: false,
    bgHeader: "from-pink-100 to-rose-100",
    accentText: "text-pink-700",
    title: "Sony WH-1000XM5 Wireless Headphones",
    brand: "Sony",
    trustSignal: "Verified seller",
  },
  {
    platform: "Croma",
    mrp: 29990,
    price: 26990,
    delivery: 99,
    platformFee: 0,
    total: 27089,
    ships: "Same day",
    score: 82,
    isNexa: false,
    bgHeader: "from-emerald-100 to-green-100",
    accentText: "text-emerald-700",
    title: "Sony WH-1000XM5 Wireless Headphones",
    brand: "Sony",
    trustSignal: "Verified seller",
  },
];

function ShoppingRoute() {
  const [phase, setPhase] = useState<'search' | 'results'>('search');
  const [searchQuery, setSearchQuery] = useState("Sony WH-1000XM5");
  const [workflowResult, setWorkflowResult] = useState<ShoppingWorkflowResult | null>(null);

  const resolvedResult = useMemo(() => {
    if (workflowResult) return workflowResult;

    return executeShoppingWorkflow(searchQuery, { city: "Bengaluru, India" });
  }, [searchQuery, workflowResult]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    const nextResult = executeShoppingWorkflow(searchQuery, { city: "Bengaluru, India" });
    setWorkflowResult(nextResult);
    setPhase('results');
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-8 pb-12 pt-4 px-4">
        
        <AnimatePresence mode="wait">
          {phase === 'search' ? (
            <motion.div
              key="search"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex min-h-[60vh] flex-col items-center justify-center text-center"
            >
              <div className="mb-4 inline-flex items-center gap-1.5 rounded-full bg-brand-soft px-3 py-1 text-[12px] font-semibold text-brand-strong uppercase tracking-wider">
                <ShoppingBag className="h-3.5 w-3.5" />
                Shopping Intelligence
              </div>
              
              <h1 className="tc-display text-4xl sm:text-5xl font-bold tracking-tight text-foreground">
                Find the real price of any product
              </h1>
              
              <form onSubmit={handleSearch} className="w-full max-w-2xl mt-8 relative group">
                <div className="absolute inset-y-0 left-0 flex items-center pl-5 pointer-events-none">
                  <Search className="h-6 w-6 text-muted-foreground" />
                </div>
                <input
                  type="text"
                  className="w-full h-16 pl-14 pr-16 rounded-2xl border-2 border-border bg-card text-[16px] shadow-[var(--elev-card)] outline-none transition-all focus:border-brand/50 focus:shadow-[0_0_0_4px_var(--color-brand-soft)]"
                  placeholder="Search or paste Amazon/Flipkart link..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button
                  type="submit"
                  className="absolute inset-y-2 right-2 grid aspect-square place-items-center rounded-xl bg-brand text-brand-foreground transition-transform hover:scale-105 active:scale-95"
                >
                  <ArrowRight className="h-6 w-6" />
                </button>
              </form>

              <div className="mt-8">
                <p className="text-[13px] text-muted-foreground mb-3">Popular searches:</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {popularSearches.map((term) => (
                    <button
                      key={term}
                      onClick={() => {
                        setSearchQuery(term);
                        setPhase('results');
                      }}
                      className="rounded-full border border-border bg-surface-2/50 px-4 py-1.5 text-[13px] font-medium text-foreground transition-colors hover:bg-surface-2 hover:border-brand/30"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              {/* HEADER SEARCH BAR */}
              <div className="flex items-center gap-4">
                <form onSubmit={handleSearch} className="flex-1 relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
                    <Search className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <input
                    type="text"
                    className="w-full h-12 pl-10 pr-12 rounded-xl border border-border bg-card text-[14px] shadow-sm outline-none transition-all focus:border-brand/50 focus:ring-2 focus:ring-brand-soft"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => setPhase('search')}
                    className="absolute inset-y-1.5 right-1.5 grid place-items-center rounded-lg px-2 text-muted-foreground hover:bg-surface-2 hover:text-foreground"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                </form>
              </div>

              {/* NEXA RECOMMENDATION */}
              <div className="flex items-start gap-4 rounded-xl border border-brand/20 bg-brand-soft/20 p-4 shadow-sm">
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-brand text-brand-foreground shadow-md">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-[16px] font-bold text-foreground">{resolvedResult.summary}</h2>
                  <p className="mt-1 text-[14px] text-muted-foreground">
                    {resolvedResult.route === "shopping-agent"
                      ? "Complexity gate routed through the shopping specialist workflow."
                      : "Direct tool execution path used for a straightforward shopping query."}
                  </p>
                </div>
              </div>

              {/* RESULTS GRID */}
              <Stagger className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-2">
                {(resolvedResult.providers ?? mockResults).map((res) => (
                  <StaggerItem key={res.platform}>
                    <div className={`relative flex flex-col overflow-hidden rounded-2xl border ${res.isNexa ? "border-positive/20 bg-positive-soft/10 shadow-md" : "border-border bg-card shadow-[var(--elev-card)]"}`}>
                      
                      {res.isNexa && (
                        <div className="absolute right-3 top-3 z-10">
                          <Tag tone="positive" className="text-[10px]" icon={<Sparkles className="h-3 w-3" />}>NEXA PICK</Tag>
                        </div>
                      )}

                      {/* Header bar */}
                      <div className={`flex h-16 items-center px-5 bg-gradient-to-r ${res.bgHeader}`}>
                        <h3 className={`text-[18px] font-bold ${res.accentText}`}>{res.platform}</h3>
                      </div>

                      {/* Content */}
                      <div className="flex flex-col p-5">
                        <div className="grid grid-cols-2 gap-y-2 text-[14px]">
                          <span className="text-muted-foreground">MRP:</span>
                          <span className="text-right font-medium line-through text-muted-foreground">{inr(res.mrp)}</span>
                          
                          <span className="text-muted-foreground">Discount:</span>
                          <span className="text-right font-medium text-positive">-{inr(res.mrp - res.price)}</span>
                          
                          <span className="text-muted-foreground">Price:</span>
                          <span className="text-right font-medium text-foreground">{inr(res.price)}</span>
                        </div>

                        <div className="my-4 h-px bg-border/60" />

                        <div className="grid grid-cols-2 gap-y-2 text-[14px]">
                          <span className="text-muted-foreground">Delivery:</span>
                          <span className="text-right font-medium">{res.delivery === 0 ? "Free" : inr(res.delivery)}</span>
                          
                          <span className="text-muted-foreground">Platform fee:</span>
                          <span className="text-right font-medium">{res.platformFee === 0 ? "₹0" : inr(res.platformFee)}</span>
                        </div>

                        <div className="my-4 h-px bg-border/60" />

                        <div className="grid grid-cols-2 items-center gap-y-3">
                          <span className="text-[16px] font-bold text-foreground">TrueCost:</span>
                          <span className="text-right flex justify-end items-center gap-1.5 text-[20px] font-bold text-foreground">
                            {inr(res.total)}
                            {res.isNexa && <Check className="h-5 w-5 text-positive" />}
                          </span>
                          
                          <span className="text-[14px] text-muted-foreground flex items-center gap-1.5">
                            <Truck className="h-4 w-4" /> Ships in:
                          </span>
                          <span className="text-right text-[14px] font-medium text-foreground">{res.ships}</span>
                        </div>

                        <button className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-foreground px-4 py-3 text-[14px] font-semibold text-background transition-transform hover:scale-[1.02] active:scale-[0.98]">
                          Buy on {res.platform} <ArrowRight className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </StaggerItem>
                ))}
              </Stagger>

              {/* SPARKLINE AREA */}
              <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-3 text-[13px] font-medium text-muted-foreground border-t border-border/50 pt-8">
                <div className="flex items-center gap-1.5">
                  <TrendingDown className="h-4 w-4 text-positive" />
                  <span>{inr(resolvedResult.evidence.savings)} below best alternative</span>
                </div>
                <span className="hidden sm:inline">·</span>
                <div className="flex items-center gap-1.5">
                  <Check className="h-4 w-4 text-brand" />
                  <span>{resolvedResult.evidence.providerCount} provider checks</span>
                </div>
                <span className="hidden sm:inline">·</span>
                <div className="flex items-center gap-1.5">
                  <TagIcon className="h-4 w-4 text-blue-500" />
                  <span>{resolvedResult.complexity.toUpperCase()} workflow</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </AppShell>
  );
}
