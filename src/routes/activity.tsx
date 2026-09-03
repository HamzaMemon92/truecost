import { createFileRoute } from "@tanstack/react-router";
import { ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/tc/app-shell";
import { BrandLogo } from "@/components/tc/brand-logo";
import { StatCard, Tag } from "@/components/tc/ui-kit";
import { inr } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/activity")({
  head: () => ({
    meta: [
      { title: "Orders & Trips — TrueCost" },
    ],
  }),
  component: Activity,
});

const tabs = ["All", "Orders", "Trips", "Upcoming", "Returns"];

const timeline = [
  {
    dateStr: "TODAY",
    provider: "Blinkit",
    name: "Blinkit Grocery",
    detail: "12 items",
    status: "Delivered",
    amount: 2435,
    saved: 465,
  },
  {
    dateStr: "TODAY",
    provider: "Uber",
    name: "Uber Go",
    detail: "Koramangala → Airport",
    status: "Completed",
    amount: 1890,
    saved: 610,
  },
  {
    dateStr: "YESTERDAY",
    provider: "Amazon",
    name: "Amazon",
    detail: "Sony Headphones",
    status: "In Transit",
    amount: 8999,
    saved: 1000,
  },
  {
    dateStr: "MAY 24",
    provider: "IndiGo",
    name: "IndiGo 6E 2031",
    detail: "BLR → DEL",
    status: "Upcoming",
    amount: 12649,
    saved: 1851,
  },
  {
    dateStr: "MAY 22",
    provider: "Zomato",
    name: "Zomato",
    detail: "Burger King",
    status: "Delivered",
    amount: 299,
  },
  {
    dateStr: "MAY 20",
    provider: "Flipkart",
    name: "Flipkart",
    detail: "Samsung TV",
    status: "Delivered",
    amount: 34999,
    saved: 5000,
  },
  {
    dateStr: "JUN 07",
    provider: "MakeMyTrip",
    name: "Goa Weekend",
    detail: "Hotel Prime Ocean",
    status: "Upcoming",
    amount: 9600,
    notes: "2 Nights",
  },
  {
    dateStr: "MAY 18",
    provider: "Rapido",
    name: "Rapido Auto",
    detail: "Office → Home",
    status: "Completed",
    amount: 89,
  },
];

const statusColors: Record<string, "positive" | "info" | "warning" | "danger" | "neutral"> = {
  "Delivered": "positive",
  "Completed": "positive",
  "In Transit": "info",
  "Upcoming": "warning",
  "Cancelled": "danger",
  "Returned": "neutral"
};

function Activity() {
  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Orders & Trips</h1>
          <p className="mt-1 text-[15px] text-muted-foreground">All your purchases, bookings and travel in one place.</p>
        </div>

        <div className="flex items-center gap-6 border-b border-border overflow-x-auto scrollbar-hide">
          {tabs.map((tab, i) => (
            <button
              key={tab}
              className={cn(
                "pb-3 text-[14px] font-semibold transition-colors whitespace-nowrap",
                i === 0 ? "border-b-2 border-brand text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        <section className="grid gap-4 sm:grid-cols-3">
          <StatCard
            label="Total spent this month"
            value={inr(47840)}
            sub="Across all connected accounts"
          />
          <StatCard
            label="Items ordered"
            value="12"
            sub="Deliveries and purchases"
          />
          <StatCard
            label="Upcoming trips"
            value="2"
            sub="Next: BLR → DEL"
          />
        </section>

        <div className="rounded-xl border border-border bg-card">
          <ul className="divide-y divide-border">
            {timeline.map((item, i) => (
              <li key={i} className="flex items-center gap-4 p-4 transition-colors hover:bg-surface-2/40 sm:p-5">
                <div className="w-20 shrink-0 text-left">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                    {item.dateStr}
                  </span>
                </div>
                
                <div className="flex min-w-0 flex-1 items-center gap-3 sm:gap-4">
                  <BrandLogo name={item.provider} size={40} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[15px] font-semibold text-foreground">
                      {item.name}
                    </p>
                    <p className="truncate text-[13px] text-muted-foreground">
                      {item.detail} {item.notes && `· ${item.notes}`}
                    </p>
                  </div>
                  <div className="hidden sm:block">
                    <Tag tone={statusColors[item.status] || "neutral"}>
                      {item.status}
                    </Tag>
                  </div>
                </div>

                <div className="shrink-0 text-right">
                  <p className="tc-num text-[16px] font-bold">{inr(item.amount)}</p>
                  {item.saved && (
                    <p className="mt-0.5 text-[11px] font-semibold text-positive">
                      Saved {inr(item.saved)}
                    </p>
                  )}
                  <div className="mt-1 sm:hidden">
                     <Tag tone={statusColors[item.status] || "neutral"}>
                      {item.status}
                    </Tag>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl border border-brand/20 bg-brand-soft/30 p-4 text-center">
          <p className="flex items-center justify-center gap-2 text-[13px] font-medium">
            <ShieldCheck className="h-4 w-4 text-brand" />
            NEXA Post-Purchase Guardian is watching your orders for price drops and delays.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
