import { createFileRoute } from "@tanstack/react-router";
import {
  Check,
  Minus,
  Plus,
  Sparkles,
  X,
  ShoppingCart,
  ShoppingBasket,
  Egg,
  Coffee,
  ArrowRight,
  RefreshCw,
  Info,
  Clock,
  Package,
  MapPin,
  Search
} from "lucide-react";
import { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/tc/app-shell";
import { Button } from "@/components/ui/button";
import { GrocerySearch } from "@/components/tc/grocery-search";
import {
  Panel,
  PageHeader,
  Tag,
  Stagger,
  StaggerItem,
  SegmentedControl,
  EmptyState
} from "@/components/tc/ui-kit";
import { cn } from "@/lib/utils";
import { inr } from "@/lib/mock-data";
import { queryGrocery, GroceryObjective } from "@/lib/api";
import { ProductCard } from "@/components/tc/product-card";
import { useBasket } from "@/lib/use-basket";
import { BasketDrawer } from "@/components/tc/basket";

export const Route = createFileRoute("/grocery")({
  head: () => ({
    meta: [
      { title: "Grocery Comparison — TrueCost" },
      {
        name: "description",
        content: "Predictive grocery comparison. Add items, we find the cheapest basket.",
      },
    ],
  }),
  component: Grocery,
});

const OBJECTIVE_OPTIONS = [
  { value: "cheapest", label: "Cheapest" },
  { value: "fastest", label: "Fastest" },
  { value: "balanced", label: "Best Value" },
] as const;

function Grocery() {
  const [query, setQuery] = useState("");
  const [objective, setObjective] = useState<GroceryObjective>("cheapest");
  const [location, setLocation] = useState("Bengaluru");
  const [isEditingLocation, setIsEditingLocation] = useState(false);
  const basket = useBasket();
  
  // Simulated Loading State
  const [loadingStep, setLoadingStep] = useState(0);
  const loadingMessages = [
    "Searching Blinkit...",
    "Searching Zepto...",
    "Searching Swiggy Instamart...",
    "Checking local availability...",
    "Finding the best deals..."
  ];

  const { data: responseData, isFetching: isPending, error, isSuccess, refetch } = useQuery({
    queryKey: ["grocerySearch", query, objective, location],
    queryFn: async ({ signal }) => {
      if (!query.trim()) return null;
      return queryGrocery([query], objective, signal);
    },
    enabled: false,
    staleTime: 60000, // keep cache for 1m
  });

  useEffect(() => {
    if (!isPending) {
      setLoadingStep(0);
      return;
    }
    const interval = setInterval(() => {
      setLoadingStep(s => (s < loadingMessages.length - 1 ? s + 1 : s));
    }, 600);
    return () => clearInterval(interval);
  }, [isPending]);

  const handleSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;
    refetch();
  };
  
  const handleRefine = (refinement: string) => {
    const newQuery = `${query} ${refinement}`.trim();
    setQuery(newQuery);
    setTimeout(() => refetch(), 0);
  };

  const productComparisons = responseData?.product_comparisons || [];

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-8 pb-20 mt-4 sm:mt-8">
        
        {/* TOP BAR: Location & Search */}
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
            <h1 className="text-2xl font-black tracking-tight text-foreground">Grocery</h1>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 rounded-xl bg-surface-2 px-4 py-2 border border-border">
                <MapPin className="h-4 w-4 text-brand" />
                {isEditingLocation ? (
                  <input 
                    autoFocus
                    type="text" 
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    onBlur={() => setIsEditingLocation(false)}
                    onKeyDown={(e) => e.key === 'Enter' && setIsEditingLocation(false)}
                    className="bg-transparent text-sm font-semibold text-foreground outline-none w-24"
                  />
                ) : (
                  <span 
                    onClick={() => setIsEditingLocation(true)}
                    className="text-sm font-semibold text-foreground cursor-pointer hover:underline"
                  >
                    Delivering to <span className="text-brand">{location}</span>
                  </span>
                )}
              </div>
              
              <div 
                onClick={() => basket.setIsOpen(true)}
                className="relative flex items-center justify-center h-10 w-10 rounded-full bg-surface-2 border border-border cursor-pointer hover:bg-surface-3 transition-colors"
              >
                <ShoppingCart className="h-5 w-5 text-foreground" />
                {basket.itemCount > 0 && (
                  <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-brand text-[10px] font-bold text-brand-foreground">
                    {basket.itemCount}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="relative z-50">
            <GrocerySearch 
              onSelectItem={(item) => {
                setQuery(item);
                setTimeout(() => refetch(), 0);
              }}
              onSelectMultiple={(items) => {
                const combined = items.map(i => `${i.qty} ${i.name}`).join(", ");
                setQuery(combined);
                setTimeout(() => refetch(), 0);
              }}
            />
          </div>
          
          {/* Refinements */}
          {query.toLowerCase().includes("milk") && !isPending && (
            <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} className="flex flex-wrap gap-2">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider py-1.5 pr-2">Refine:</span>
              {["Amul", "Mother Dairy", "1 L", "500 ml", "Full Cream", "Toned"].map(r => (
                <button 
                  key={r}
                  onClick={() => handleRefine(r)}
                  className="rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground hover:border-brand hover:text-brand transition-colors"
                >
                  {r}
                </button>
              ))}
            </motion.div>
          )}
        </div>

        {/* MAIN: Results */}
        <div className="pt-4">
          {error && (
            <div className="p-4 bg-danger-soft border border-danger/30 text-danger text-sm rounded-xl font-medium mb-6">
              {error.message}
            </div>
          )}
          
          {responseData?.observability && responseData.observability.some((o: any) => o.status !== "success") && (
            <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 text-yellow-600 text-sm rounded-xl font-medium mb-6 flex items-start gap-3">
              <Info className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Partial Results</p>
                <p className="opacity-90">Compared {responseData.observability.filter((o: any) => o.status === "success").length} of {responseData.observability.length} retailers. Some retailers are currently experiencing delays or are unavailable.</p>
              </div>
            </div>
          )}

          {isPending ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <RefreshCw className="h-8 w-8 animate-spin text-brand" />
              <p className="font-semibold text-muted-foreground animate-pulse">{loadingMessages[loadingStep]}</p>
            </div>
          ) : isSuccess ? (
            productComparisons.length > 0 ? (
              <div className="space-y-6">
                <div className="flex items-center justify-between border-b border-border/50 pb-4">
                  <h2 className="text-xl font-bold tracking-tight">Search Results</h2>
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">Sort By</span>
                    <SegmentedControl
                      options={OBJECTIVE_OPTIONS}
                      value={objective}
                      onChange={(val) => {
                        setObjective(val as GroceryObjective);
                        setTimeout(() => refetch(), 0);
                      }}
                      className="w-auto p-1 bg-surface-2"
                    />
                  </div>
                </div>

                <Stagger className="space-y-6">
                  {productComparisons.map((comp: any) => (
                    <StaggerItem key={comp.product.canonical_product_id}>
                      <ProductCard 
                        comparison={comp} 
                        onAdd={(resolvedImageUrl) => {
                          const item: any = {
                            canonical_product_id: comp.product.canonical_product_id,
                            title: comp.product.title,
                            variant: comp.product.variant
                          };
                          if (resolvedImageUrl) {
                            item.image_url = resolvedImageUrl;
                          }
                          basket.addItem(item, 1);
                        }}
                      />
                    </StaggerItem>
                  ))}
                </Stagger>
              </div>
            ) : (
              <EmptyState 
                title="No Exact Matches"
                body="We couldn't find exact matches for your search in this area. Try adjusting your query or location."
                icon={<Search className="h-6 w-6" />}
              />
            )
          ) : (
            <div className="flex flex-col items-center justify-center py-20 opacity-50">
              <ShoppingBasket className="h-16 w-16 text-muted-foreground mb-4" />
              <h2 className="text-xl font-bold tracking-tight">Start your grocery search</h2>
              <p className="text-muted-foreground mt-2">Find the best prices across Blinkit, Zepto, and Swiggy Instamart</p>
            </div>
          )}
        </div>
      </div>
      <BasketDrawer 
        isOpen={basket.isOpen}
        onClose={() => basket.setIsOpen(false)}
        items={basket.items}
        location={location}
        updateQuantity={basket.updateQuantity}
        removeItem={basket.removeItem}
      />
    </AppShell>
  );
}
