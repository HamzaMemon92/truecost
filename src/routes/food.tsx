import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { 
  ChevronRight, 
  Clock, 
  MapPin, 
  Search, 
  Sparkles, 
  Star, 
  UtensilsCrossed, 
  Zap 
} from "lucide-react";
import { motion } from "framer-motion";
import { AppShell } from "@/components/tc/app-shell";
import { Panel, Tag, Stagger, StaggerItem } from "@/components/tc/ui-kit";
import { inr } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/food")({
  head: () => ({
    meta: [
      { title: "Food — TrueCost" },
      {
        name: "description",
        content: "Find the best TrueCost for your food delivery orders.",
      },
    ],
  }),
  component: Food,
});

const cuisines = ["All", "Pizza", "Burgers", "Chinese", "Healthy", "Indian"];

const quickReorders = [
  { id: 1, food: "Butter Chicken", restaurant: "Burger King", color: "bg-orange-500" },
  { id: 2, food: "Margherita Pizza", restaurant: "Domino's", color: "bg-red-500" },
  { id: 3, food: "Pad Thai", restaurant: "PF Chang's", color: "bg-amber-500" },
];

const restaurants = [
  {
    name: "Burger King",
    location: "Koramangala",
    best: "Zomato",
    decisionScore: 87,
    reason: "₹10 cheaper on Zomato despite 5 min longer",
    gradient: "from-orange-100 to-amber-200",
    options: [
      {
        provider: "Swiggy",
        item: 249,
        delivery: 30,
        platform: 15,
        total: 294,
        eta: "35 min",
        rating: 4.2,
      },
      {
        provider: "Zomato",
        item: 249,
        delivery: 25,
        platform: 10,
        total: 284,
        eta: "40 min",
        rating: 4.2,
      },
    ],
  },
  {
    name: "Domino's Pizza",
    location: "Indiranagar",
    best: "Swiggy",
    decisionScore: 92,
    reason: "Free delivery on Swiggy today — saves ₹35",
    gradient: "from-red-100 to-rose-200",
    options: [
      {
        provider: "Swiggy",
        item: 399,
        delivery: 0,
        platform: 5,
        total: 404,
        eta: "30 min",
        rating: 4.5,
      },
      {
        provider: "Zomato",
        item: 399,
        delivery: 30,
        platform: 10,
        total: 439,
        eta: "35 min",
        rating: 4.4,
      },
    ],
  },
  {
    name: "McDonald's",
    location: "Whitefield",
    best: "Zomato",
    decisionScore: 89,
    reason: "₹50 cheaper on Zomato with zero fees today",
    gradient: "from-yellow-100 to-amber-100",
    options: [
      {
        provider: "Swiggy",
        item: 319,
        delivery: 20,
        platform: 10,
        total: 349,
        eta: "25 min",
        rating: 4.3,
      },
      {
        provider: "Zomato",
        item: 299,
        delivery: 0,
        platform: 0,
        total: 299,
        eta: "30 min",
        rating: 4.4,
      },
    ],
  },
  {
    name: "Barbeque Nation",
    location: "Marathahalli",
    best: "Swiggy",
    decisionScore: 85,
    reason: "Swiggy Pro free delivery saves ₹50",
    gradient: "from-rose-100 to-pink-200",
    options: [
      {
        provider: "Swiggy",
        item: 899,
        delivery: 0,
        platform: 9,
        total: 908,
        eta: "45 min",
        rating: 4.6,
      },
      {
        provider: "Zomato",
        item: 899,
        delivery: 49,
        platform: 10,
        total: 958,
        eta: "50 min",
        rating: 4.5,
      },
    ],
  },
];

function Food() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCuisine, setSelectedCuisine] = useState("All");

  const filteredRestaurants = restaurants.filter(r => 
    r.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <AppShell>
      <div className="space-y-8 pb-12">
        {/* TOP SECTION — Hero search bar */}
        <section className="space-y-4">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-1.5 text-muted-foreground font-medium">
              <MapPin className="h-4 w-4" />
              <span>Koramangala, Bangalore</span>
              <button className="ml-1 text-brand hover:underline text-[13px]">
                [change]
              </button>
            </div>
            <Tag tone="brand" className="text-[10px] tracking-wider uppercase">
              Before you order, ask Nexa
            </Tag>
          </div>

          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search restaurants, dishes..."
              className="w-full rounded-2xl border border-border bg-card py-4 pl-12 pr-4 text-[16px] shadow-sm transition-all focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-2">
            {cuisines.map((c) => (
              <button
                key={c}
                onClick={() => setSelectedCuisine(c)}
                className={cn(
                  "rounded-full px-4 py-2 text-[14px] font-medium transition-colors",
                  selectedCuisine === c
                    ? "bg-brand text-brand-foreground"
                    : "border border-border bg-card hover:bg-surface-2 text-muted-foreground"
                )}
              >
                {c}
              </button>
            ))}
          </div>

        </section>

        {/* ⚡ Zomato Coupon Alert */}
        <section>
          <div className="flex items-center gap-3 rounded-xl border border-brand/20 bg-brand-soft/20 px-4 py-3 dark:border-brand/40">
            <Sparkles className="h-4 w-4 shrink-0 text-brand" />
            <p className="flex-1 text-[12px] font-semibold text-foreground">
              <span className="font-bold text-brand">Offer active</span> — ₹80 off on Domino's via Zomato for you. Expires at 11 PM tonight.
            </p>
            <Tag tone="brand" className="text-[10px] shrink-0">Live</Tag>
          </div>
        </section>

        {/* QUICK REORDER strip */}
        <section>
          <h3 className="text-[15px] font-bold mb-3 flex items-center gap-2">
            <Zap className="h-4 w-4 text-warning fill-warning" />
            Your usual
          </h3>
          <div className="flex items-center gap-3 overflow-x-auto pb-4 scrollbar-hide">
            {quickReorders.map((item) => (
              <motion.div
                key={item.id}
                whileHover={{ y: -2 }}
                className="flex-shrink-0 flex items-center gap-3 rounded-xl border border-border bg-card p-3 shadow-sm min-w-[240px]"
              >
                <div className={cn("h-3 w-3 rounded-full", item.color)} />
                <div className="flex-1 min-w-0">
                  <p className="text-[14px] font-bold truncate">{item.food}</p>
                  <p className="text-[12px] text-muted-foreground truncate">{item.restaurant}</p>
                </div>
                <button className="rounded-full bg-surface-2 px-3 py-1.5 text-[12px] font-semibold transition-colors hover:bg-brand hover:text-brand-foreground">
                  Reorder
                </button>
              </motion.div>
            ))}
          </div>
        </section>

        {/* RESULTS — Restaurant cards */}
        <section className="space-y-4">
          <Stagger>
            {filteredRestaurants.map((restaurant) => (
              <StaggerItem key={restaurant.name}>
                <motion.div
                  whileHover={{ y: -4 }}
                  className="group relative flex flex-col md:flex-row overflow-hidden rounded-2xl border border-border bg-card shadow-[var(--elev-card)] transition-shadow hover:shadow-[var(--elev-raised)]"
                >
                  {/* Left Gradient Area */}
                  <div className={cn(
                    "flex md:w-[160px] md:shrink-0 items-center justify-center p-6 bg-gradient-to-br",
                    restaurant.gradient
                  )}>
                    <UtensilsCrossed className="h-12 w-12 text-black/10 mix-blend-overlay" />
                  </div>

                  {/* Right Content */}
                  <div className="flex flex-1 flex-col p-4 sm:p-5">
                    <div className="flex items-start justify-between">
                      <div>
                        <h2 className="text-[18px] font-bold">{restaurant.name}</h2>
                        <div className="mt-1 flex items-center gap-2 text-[13px] text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Star className="h-3.5 w-3.5 fill-warning text-warning" />
                            4.5
                          </span>
                          <span>·</span>
                          <span>{restaurant.location}</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-center h-10 w-10 rounded-full border border-brand/20 bg-brand-soft/30 text-brand font-bold tc-num">
                        {restaurant.decisionScore}
                      </div>
                    </div>

                    <div className="mt-3 inline-flex items-center gap-1.5 text-[13px] font-medium text-brand">
                      <Sparkles className="h-4 w-4" />
                      NEXA: {restaurant.reason}
                    </div>

                    <div className="mt-5 grid grid-cols-2 gap-3">
                      {restaurant.options.map((opt) => {
                        const isPick = opt.provider === restaurant.best;
                        return (
                          <div
                            key={opt.provider}
                            className={cn(
                              "relative flex flex-col justify-between rounded-xl border p-3.5 transition-colors",
                              isPick
                                ? "border-positive/30 bg-positive-soft/20"
                                : "border-border bg-surface-1"
                            )}
                          >
                            {isPick && (
                              <div className="absolute -top-2.5 right-3">
                                <Tag tone="positive" className="text-[10px] px-2 py-0.5 shadow-sm">
                                  NEXA PICK
                                </Tag>
                              </div>
                            )}
                            
                            <div>
                              <div className="flex items-center gap-1.5 font-bold text-[14px] mb-2">
                                {opt.provider}
                                {isPick && <span className="text-positive">✓</span>}
                              </div>
                              <div className="space-y-1 text-[12px] text-muted-foreground">
                                <div className="flex justify-between">
                                  <span>Food:</span>
                                  <span className="tc-num">{inr(opt.item)}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Del:</span>
                                  <span className="tc-num">{opt.delivery === 0 ? "Free" : inr(opt.delivery)}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Platform fee:</span>
                                  <span className="tc-num">{inr(opt.platform)}</span>
                                </div>
                              </div>
                            </div>
                            
                            <div className="mt-3 pt-3 border-t border-border/50">
                              <div className="flex items-center justify-between font-bold">
                                <span className="text-[13px]">TOTAL</span>
                                <span className="text-[16px] tc-num">{inr(opt.total)}</span>
                              </div>
                              <div className="mt-1 flex items-center gap-1 text-[11px] text-muted-foreground">
                                <Clock className="h-3 w-3" />
                                {opt.eta}
                              </div>
                              
                              <button className={cn(
                                "mt-3 w-full rounded-lg py-2 text-[13px] font-bold transition-all flex items-center justify-center gap-1",
                                isPick
                                  ? "bg-brand text-brand-foreground hover:bg-brand-strong hover:shadow-md"
                                  : "bg-surface-2 text-foreground hover:bg-surface-3 border border-border"
                              )}>
                                Order {opt.provider}
                                <ChevronRight className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </motion.div>
              </StaggerItem>
            ))}
          </Stagger>
        </section>
      </div>
    </AppShell>
  );
}
