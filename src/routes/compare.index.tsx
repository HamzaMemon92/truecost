import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import {
  Car,
  Plane,
  ShoppingBasket,
  Building2,
  UtensilsCrossed,
  ShoppingBag,
  Tag as TagIcon,
  MoreHorizontal,
  ChevronRight,
  Search,
  ArrowRight,
  Sparkles,
  Clock,
  Smartphone,
  Check
} from "lucide-react";
import { motion } from "framer-motion";
import { AppShell } from "@/components/tc/app-shell";
import {
  AnimatedNumber,
  Panel,
  Stagger,
  StaggerItem,
  Tag,
} from "@/components/tc/ui-kit";
import { inr } from "@/lib/mock-data";

export const Route = createFileRoute("/compare/")({
  head: () => ({
    meta: [
      { title: "Compare Anything — TrueCost" },
      {
        name: "description",
        content: "Compare products, rides, groceries and travel based on real fee-inclusive TrueCost.",
      },
    ],
  }),
  component: CompareHub,
});

const categories = [
  { label: "Rides",    to: "/compare/rides" as const, icon: Car,            gradient: "from-zinc-100 to-slate-200",     iconColor: "text-zinc-700",    tagline: "Uber vs Ola vs Rapido",           isPopular: true },
  { label: "Flights",  to: "/travel"        as const, icon: Plane,          gradient: "from-sky-100 to-blue-200",       iconColor: "text-sky-600",     tagline: "All airlines compared" },
  { label: "Grocery", to: "/grocery"       as const, icon: ShoppingBasket, gradient: "from-green-100 to-emerald-200",    iconColor: "text-emerald-600", tagline: "Blinkit vs Zepto vs Instamart",  isPopular: true },
  { label: "Hotels",  to: "/hotels"        as const, icon: Building2,      gradient: "from-amber-100 to-orange-200",   iconColor: "text-amber-600",   tagline: "All platforms compared" },
  { label: "Food",    to: "/food"          as const, icon: UtensilsCrossed, gradient: "from-red-100 to-rose-200",        iconColor: "text-rose-600",    tagline: "Swiggy vs Zomato" },
  { label: "Shopping",to: "/shopping"      as const, icon: ShoppingBag,    gradient: "from-violet-100 to-purple-200",  iconColor: "text-violet-600",  tagline: "Amazon vs Flipkart" },
  { label: "Deals",   to: "/deals"         as const, icon: TagIcon,        gradient: "from-teal-100 to-cyan-200",      iconColor: "text-teal-600",    tagline: "AI-curated drops" },
  { label: "More",    to: "/compare"       as const, icon: MoreHorizontal, gradient: "from-slate-100 to-slate-200",    iconColor: "text-slate-400",   tagline: "Coming soon" },
];

const recentSearches = [
  { label: "Airport ride", time: "2h ago", icon: Car },
  { label: "Domino's Pizza", time: "4h ago", icon: UtensilsCrossed },
  { label: "Hotel Mumbai", time: "1d ago", icon: Building2 },
  { label: "OnePlus 12", time: "2d ago", icon: Smartphone },
];

function CompareHub() {
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // route appropriately based on intent
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-12 pb-12 pt-4">
        
        {/* HERO AREA */}
        <section className="text-center px-4">
          <h1 className="tc-display text-4xl sm:text-5xl font-bold tracking-tight text-foreground">
            Compare anything.<br/>
            <span className="text-brand">NEXA finds the smartest choice.</span>
          </h1>
          <p className="mt-4 text-[15px] text-muted-foreground">
            Find the real TrueCost for products, rides, travel, and more.
          </p>

          <form onSubmit={handleSearch} className="mx-auto mt-8 max-w-2xl relative group">
            <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
              <Search className="h-5 w-5 text-muted-foreground" />
            </div>
            <input
              type="text"
              className="w-full h-14 pl-12 pr-14 rounded-2xl border-2 border-border bg-surface-2/50 text-[15px] outline-none transition-all focus:border-brand/50 focus:bg-card focus:shadow-[0_0_0_4px_var(--color-brand-soft)]"
              placeholder="Search: paste a link or type a product name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button
              type="submit"
              className="absolute inset-y-1.5 right-1.5 grid aspect-square place-items-center rounded-xl bg-brand text-brand-foreground transition-transform hover:scale-105 active:scale-95"
            >
              <ArrowRight className="h-5 w-5" />
            </button>
          </form>
          <p className="mt-6 text-[13px] font-medium text-muted-foreground uppercase tracking-widest">
            Or choose a category
          </p>
        </section>

        {/* CATEGORY GRID */}
        <div className="px-4">
          <Stagger className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {categories.map((cat) => {
              const Icon = cat.icon;
              return (
                <StaggerItem key={cat.label}>
                  <Link
                    to={cat.to}
                    className="group relative flex flex-col rounded-2xl border border-border bg-card p-5 transition-all hover:-translate-y-1 hover:border-brand/20 hover:shadow-md h-full"
                  >
                    {cat.isPopular && (
                      <div className="absolute right-3 top-3 z-10">
                        <Tag tone="brand" className="text-[10px]">Most popular</Tag>
                      </div>
                    )}
                    <div className={`mb-4 flex h-20 items-center justify-center rounded-xl bg-gradient-to-br ${cat.gradient}`}>
                      <Icon className={`h-9 w-9 transition-transform duration-300 group-hover:scale-110 ${cat.iconColor}`} />
                    </div>
                    <h3 className="text-[15px] font-bold text-foreground">{cat.label}</h3>
                    <div className="mt-0.5 flex items-center justify-between">
                      <p className="text-[12px] text-muted-foreground truncate pr-2">{cat.tagline}</p>
                      <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-brand" />
                    </div>
                  </Link>
                </StaggerItem>
              );
            })}
          </Stagger>
        </div>

        {/* STATS STRIP */}
        <section className="px-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Panel className="flex flex-col items-center justify-center p-6 text-center" elevation="flat">
              <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-positive/10 text-positive">
                <Sparkles className="h-5 w-5" />
              </div>
              <p className="tc-num text-2xl font-bold text-foreground">
                ₹<AnimatedNumber value={31240} />
              </p>
              <p className="text-[13px] text-muted-foreground">Saved this month</p>
            </Panel>
            <Panel className="flex flex-col items-center justify-center p-6 text-center" elevation="flat">
              <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-brand-soft/50 text-brand">
                <Check className="h-5 w-5" />
              </div>
              <p className="tc-num text-2xl font-bold text-foreground">
                <AnimatedNumber value={847} />
              </p>
              <p className="text-[13px] text-muted-foreground">Decisions made</p>
            </Panel>
            <Panel className="flex flex-col items-center justify-center p-6 text-center" elevation="flat">
              <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                <Building2 className="h-5 w-5" />
              </div>
              <p className="tc-num text-2xl font-bold text-foreground">
                <AnimatedNumber value={12} />
              </p>
              <p className="text-[13px] text-muted-foreground">Categories</p>
            </Panel>
          </div>
        </section>

        {/* RECENT ACTIVITY */}
        <section className="px-4">
          <div className="mb-3 flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-[14px] font-semibold text-foreground">Recently compared</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {recentSearches.map((s, i) => {
              const Icon = s.icon;
              return (
                <button
                  key={i}
                  className="flex items-center gap-2 rounded-full border border-border bg-surface-2/50 px-3 py-1.5 transition-colors hover:bg-surface-2 hover:border-brand/30"
                >
                  <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-[13px] font-medium">{s.label}</span>
                  <span className="text-[11px] text-muted-foreground">· {s.time}</span>
                </button>
              );
            })}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
