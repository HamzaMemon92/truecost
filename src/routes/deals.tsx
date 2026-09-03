import { createFileRoute } from "@tanstack/react-router";
import { ArrowRight, Clock, Plane, ShoppingBag, Smartphone, Sparkles, Tag as TagIcon, Utensils, Zap } from "lucide-react";
import { AppShell } from "@/components/tc/app-shell";
import { Tag } from "@/components/tc/ui-kit";
import { inr } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/deals")({
  head: () => ({
    meta: [
      { title: "Deals — TrueCost" },
    ],
  }),
  component: Deals,
});

const tabs = ["For You", "Today's Drops", "Flash Sales", "Expiring Soon"];

const deals = [
  {
    category: "Electronics",
    icon: Smartphone,
    name: "Sony WH-1000XM5",
    insight: "₹5,000 below Amazon average",
    price: 24990,
    saving: 5000,
    decisionScore: 93,
    action: "BUY",
    why: "Price dropped significantly in the last 24h. Historically, it bounces back within 3 days.",
  },
  {
    category: "Travel",
    icon: Plane,
    name: "BLR → DEL",
    insight: "Lowest in 45 days for this route",
    price: 3299,
    saving: 1200,
    decisionScore: 91,
    action: "BOOK",
    why: "Booking window is optimal. Waiting closer to departure dates will increase fares.",
  },
  {
    category: "Groceries",
    icon: ShoppingBag,
    name: "Milk + Eggs + Bread basket",
    insight: "₹184 cheaper on Zepto today",
    price: 195,
    saving: 184,
    decisionScore: null,
    action: "BUY",
    why: "Zepto is running a 40% off dairy promotion today.",
  },
  {
    category: "Electronics",
    icon: Smartphone,
    name: "Samsung Galaxy S24",
    insight: "Price dropped ₹4k this week",
    price: 55999,
    saving: 4000,
    decisionScore: 88,
    action: "BUY",
    why: "New S-series announcement caused a temporary drop.",
  },
  {
    category: "Hotels",
    icon: TagIcon,
    name: "Goa Hotel",
    insight: "Weekend rate 23% below weekday",
    price: 3200,
    saving: 950,
    decisionScore: null,
    action: "BOOK",
    why: "Unusual pricing inversion. Hotels are usually more expensive on weekends.",
  },
  {
    category: "Rides",
    icon: Zap,
    name: "Rapido Auto (to Whitefield)",
    insight: "₹31 cheaper than Uber today",
    price: 89,
    saving: 31,
    decisionScore: null,
    action: "BOOK",
    why: "Uber is surging right now. Rapido is at base fare.",
  },
  {
    category: "Electronics",
    icon: Smartphone,
    name: "MacBook Air M2",
    insight: "₹9,100 below launch price",
    price: 79900,
    saving: 9100,
    decisionScore: 95,
    action: "WATCH → BUY",
    why: "M3 release pushed M2 prices down. Excellent value.",
  },
  {
    category: "Food",
    icon: Utensils,
    name: "Domino's on Zomato",
    insight: "30% off + free delivery today",
    price: 299,
    saving: 150,
    expires: "4h 23m",
    decisionScore: null,
    action: "ORDER",
    why: "Flash promotion stack. Usually only get one or the other.",
  },
];

function Deals() {
  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Deals</h1>
          <p className="mt-1 text-[15px] text-muted-foreground">AI-curated price opportunities, not coupons.</p>
        </div>

        <div className="flex items-center gap-6 border-b border-border">
          {tabs.map((tab, i) => (
            <button
              key={tab}
              className={cn(
                "pb-3 text-[14px] font-semibold transition-colors",
                i === 0 ? "border-b-2 border-brand text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {deals.map((deal) => {
            const Icon = deal.icon;
            return (
              <div
                key={deal.name}
                className="group flex flex-col justify-between overflow-hidden rounded-2xl border border-border bg-card p-5 transition-all hover:-translate-y-1 hover:border-brand/30 hover:shadow-[var(--elev-card)]"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Icon className="h-4 w-4" />
                      <span className="text-[12px] font-medium uppercase tracking-wider">{deal.category}</span>
                    </div>
                    {deal.expires && (
                      <span className="flex items-center gap-1 rounded-full bg-danger/10 px-2 py-0.5 text-[11px] font-bold text-danger">
                        <Clock className="h-3 w-3" />
                        Ends in {deal.expires}
                      </span>
                    )}
                  </div>
                  
                  <h3 className="mt-3 text-[16px] font-bold leading-snug">{deal.name}</h3>
                  
                  <div className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-brand-soft/50 px-2.5 py-1.5 text-[12px] font-medium text-foreground border border-brand/20">
                    <Sparkles className="h-3.5 w-3.5 text-brand shrink-0" />
                    <span>{deal.insight}</span>
                  </div>
                </div>

                <div className="mt-5 space-y-4">
                  <div className="flex items-end justify-between border-t border-border/70 pt-4">
                    <div>
                      <span className="tc-num text-[22px] font-bold text-foreground leading-none">
                        {inr(deal.price)}
                      </span>
                      <p className="mt-1 text-[11px] font-semibold text-positive">
                        Save {inr(deal.saving)}
                      </p>
                    </div>
                    {deal.decisionScore && (
                      <div className="text-right">
                        <span className="block text-[10px] font-medium text-muted-foreground uppercase">Score</span>
                        <span className="tc-num text-[18px] font-bold text-brand leading-none">
                          {deal.decisionScore}
                        </span>
                      </div>
                    )}
                  </div>

                  <details className="group/details">
                    <summary className="flex cursor-pointer items-center gap-1 text-[12px] font-semibold text-muted-foreground hover:text-foreground list-none">
                      Why this deal? <ArrowRight className="h-3 w-3 transition-transform group-open/details:rotate-90" />
                    </summary>
                    <p className="mt-2 text-[12px] text-muted-foreground leading-relaxed pl-4 border-l-2 border-border">
                      {deal.why}
                    </p>
                  </details>

                  <button className="w-full rounded-xl bg-brand py-2.5 text-[13px] font-bold text-brand-foreground transition-colors hover:bg-brand-strong">
                    {deal.action}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}
