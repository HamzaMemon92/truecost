import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  ArrowRight,
  Building2,
  Calendar,
  Check,
  ChevronDown,
  Edit2,
  Heart,
  MapPin,
  Search,
  Sparkles,
  Star,
  Users
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { AppShell } from "@/components/tc/app-shell";
import { Tag, Panel, Stagger, StaggerItem } from "@/components/tc/ui-kit";
import { inr } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/hotels")({
  head: () => ({
    meta: [
      { title: "Hotels — TrueCost" },
    ],
  }),
  component: Hotels,
});

const mockHotels = [
  {
    id: 1,
    name: "Taj Mahal Palace",
    stars: 5,
    location: "Apollo Bunder",
    distance: "1.2km",
    room: "Superior Room",
    platforms: [
      { name: "MakeMyTrip", price: 12499, isLowest: true },
      { name: "Booking.com", price: 13200, isLowest: false },
      { name: "Agoda", price: 13500, isLowest: false },
    ],
    lowestPlatform: "MakeMyTrip",
    lowestPrice: 12499,
    trueCost: 14748,
    cancellation: "Free cancellation",
    freeCancel: true,
    breakfast: true,
    score: 91,
    isNexaPick: false,
    gradient: "from-amber-100 to-orange-200",
  },
  {
    id: 2,
    name: "Trident Nariman Point",
    stars: 5,
    location: "Nariman Point",
    distance: "1.2km",
    room: "Superior Room",
    platforms: [
      { name: "MakeMyTrip", price: 9200, isLowest: true },
      { name: "Booking.com", price: 9800, isLowest: false },
      { name: "Agoda", price: 10100, isLowest: false },
    ],
    lowestPlatform: "MakeMyTrip",
    lowestPrice: 9200,
    trueCost: 10864,
    cancellation: "Free cancellation",
    freeCancel: true,
    breakfast: true,
    score: 88,
    isNexaPick: true,
    gradient: "from-brand-soft/60 to-violet-100",
  },
  {
    id: 3,
    name: "ITC Grand Central",
    stars: 5,
    location: "Parel",
    distance: "6.8km",
    room: "Executive Club",
    platforms: [
      { name: "MakeMyTrip", price: 8200, isLowest: false },
      { name: "Booking.com", price: 8500, isLowest: false },
      { name: "Agoda", price: 7800, isLowest: true },
    ],
    lowestPlatform: "Agoda",
    lowestPrice: 7800,
    trueCost: 9204,
    cancellation: "Non-refundable",
    freeCancel: false,
    breakfast: true,
    score: 85,
    isNexaPick: false,
    gradient: "from-slate-100 to-blue-100",
  },
  {
    id: 4,
    name: "Novotel Mumbai Juhu",
    stars: 4,
    location: "Juhu",
    distance: "18km",
    room: "Superior Room",
    platforms: [
      { name: "MakeMyTrip", price: 6100, isLowest: false },
      { name: "Booking.com", price: 5400, isLowest: true },
      { name: "Agoda", price: 5800, isLowest: false },
    ],
    lowestPlatform: "Booking.com",
    lowestPrice: 5400,
    trueCost: 6372,
    cancellation: "Free cancellation",
    freeCancel: true,
    breakfast: true,
    score: 82,
    isNexaPick: false,
    gradient: "from-emerald-50 to-teal-100",
  },
];

const popularDestinations = ["Goa", "Mumbai", "Delhi", "Jaipur", "Manali", "Dubai"];
const smartFilters = ["Price ↕", "Rating ↕", "Free Cancel", "Pool", "Breakfast"];

function Hotels() {
  const [phase, setPhase] = useState<'search' | 'results'>('search');
  const [destination, setDestination] = useState("Mumbai, India");
  const [checkIn] = useState("23 May");
  const [checkOut] = useState("25 May");
  const [adults] = useState("2 Adults");

  return (
    <AppShell>
      <div className="relative min-h-[calc(100vh-6rem)]">
        <AnimatePresence mode="wait">
          {phase === 'search' ? (
            <motion.div
              key="search"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="flex min-h-[70vh] flex-col items-center justify-center px-4"
            >
              <div className="mb-8 text-center">
                <p className="mb-3 text-[12px] font-bold uppercase tracking-[0.15em] text-brand">Hotel Intelligence</p>
                <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">Compare hotel prices across every platform</h1>
              </div>

              <Panel padded className="w-full max-w-3xl space-y-4 shadow-xl">
                <div className="relative">
                  <div className="mb-2 text-[13px] font-semibold text-muted-foreground">Where are you going?</div>
                  <div className="relative">
                    <Search className="absolute left-4 top-1/2 h-6 w-6 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="text"
                      value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                      className="w-full rounded-2xl border border-border bg-surface py-5 pl-14 pr-4 text-2xl font-bold transition-colors focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-border/50">
                  <div className="relative flex items-center">
                    <Calendar className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                    <div className="flex w-full items-center justify-between rounded-xl border border-border bg-surface py-4 pl-12 pr-4 transition-colors hover:bg-surface-2">
                      <div className="flex gap-2">
                        <span className="text-[15px] font-bold">Check-in: {checkIn}</span>
                        <span className="text-muted-foreground">→</span>
                        <span className="text-[15px] font-bold">Check-out: {checkOut}</span>
                      </div>
                      <Tag tone="brand" className="font-bold text-[12px]">2N</Tag>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <button className="flex w-full items-center justify-between rounded-xl border border-border bg-surface px-4 py-4 text-[15px] font-bold transition-colors hover:bg-surface-2">
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span>{adults}</span>
                      </div>
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    </button>
                    <button className="flex w-full items-center justify-between rounded-xl border border-border bg-surface px-4 py-4 text-[15px] font-bold transition-colors hover:bg-surface-2">
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-muted-foreground" />
                        <span>1 Room</span>
                      </div>
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    </button>
                  </div>
                </div>

                <button
                  onClick={() => setPhase('results')}
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-5 text-[18px] font-bold text-brand-foreground transition-all hover:bg-brand-strong hover:shadow-[var(--shadow-glow)]"
                >
                  Search Hotels <ArrowRight className="h-5 w-5" />
                </button>
              </Panel>

              <div className="mt-8 flex flex-wrap justify-center gap-3">
                {popularDestinations.map((city) => (
                  <button key={city} className="flex items-center gap-1.5 rounded-full border border-border/50 bg-surface/50 px-4 py-2 text-[14px] font-medium transition-colors hover:bg-surface hover:text-brand">
                    <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                    {city}
                  </button>
                ))}
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="mx-auto max-w-4xl space-y-6 pb-20 pt-4"
            >
              {/* Compact sticky search bar */}
              <div className="sticky top-4 z-20 flex items-center justify-between rounded-2xl border border-border bg-card/80 p-4 shadow-sm backdrop-blur-md">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="text-[15px] font-bold flex items-center gap-2">
                      {destination} · {checkIn}–{checkOut} · {adults}
                      <button onClick={() => setPhase('search')} className="text-muted-foreground hover:text-brand transition-colors">
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                    </p>
                    <p className="text-[13px] font-medium text-muted-foreground mt-0.5">
                      4 hotels found
                    </p>
                  </div>
                </div>
              </div>

              {/* NEXA Pick Banner */}
              <Panel accent padded className="bg-brand-soft/10 border-brand/20 shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand/10">
                      <Sparkles className="h-3.5 w-3.5 text-brand" />
                    </div>
                    <div>
                      <p className="text-[15px] font-semibold text-foreground">
                        <span className="font-bold">NEXA recommends Trident Nariman Point</span>
                      </p>
                      <p className="text-[14px] text-muted-foreground mt-0.5">
                        MakeMyTrip has ₹800 off today · Free cancellation included
                      </p>
                    </div>
                  </div>
                  <button className="flex items-center gap-1.5 rounded-lg border border-border bg-surface px-3 py-1.5 text-[13px] font-semibold transition-colors hover:bg-surface-2 hover:text-brand">
                    View hotel <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </Panel>

              {/* Hotel result cards */}
              <Stagger className="space-y-6">
                {mockHotels.map((hotel) => (
                  <StaggerItem key={hotel.id}>
                    <Panel
                      padded={false}
                      accent={hotel.isNexaPick}
                      className="group flex flex-col overflow-hidden sm:flex-row transition-all hover:shadow-md"
                    >
                      {/* Left: Gradient Hero Area (200px tall as specified) */}
                      <div className={cn("relative h-[200px] sm:h-auto sm:w-[280px] shrink-0 bg-gradient-to-br", hotel.gradient)}>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <Building2 className="h-16 w-16 text-foreground/10" />
                        </div>
                        <button className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-background/50 backdrop-blur-sm transition-colors hover:bg-background/80 hover:text-brand">
                          <Heart className="h-4 w-4" />
                        </button>
                      </div>

                      {/* Right: Details */}
                      <div className="flex flex-1 flex-col p-6">
                        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
                          <div className="flex-1 space-y-2">
                            <div className="flex items-center gap-2">
                              <h3 className="text-[20px] font-bold">{hotel.name}</h3>
                              <div className="flex">
                                {Array(hotel.stars).fill(0).map((_, i) => (
                                  <Star key={i} className="h-4 w-4 fill-amber-400 text-amber-400" />
                                ))}
                              </div>
                            </div>
                            <p className="text-[14px] text-muted-foreground">
                              {hotel.location} · {hotel.distance}
                            </p>
                            
                            <div className="flex items-center gap-2 pt-1 text-[13px] font-medium text-muted-foreground">
                              {hotel.freeCancel && <span className="flex items-center gap-1"><Check className="h-3.5 w-3.5 text-positive" /> Free cancellation</span>}
                              {!hotel.freeCancel && <span>Non-refundable</span>}
                              <span>·</span>
                              {hotel.breakfast && <span>Breakfast incl.</span>}
                              <span>·</span>
                              <span>Score {hotel.score}</span>
                            </div>
                          </div>

                          {/* Price Comparison */}
                          <div className="flex flex-col gap-2 sm:w-[220px] shrink-0">
                            <div className="space-y-1.5">
                              {hotel.platforms.map((p) => (
                                <div key={p.name} className="flex items-center justify-between">
                                  <span className="text-[13px] text-muted-foreground">
                                    {p.name}
                                  </span>
                                  <div className="flex items-center gap-2">
                                    <span className={cn("tc-num text-[14px]", p.isLowest ? "font-bold text-foreground" : "font-medium text-muted-foreground")}>
                                      {inr(p.price)}
                                    </span>
                                    {p.isLowest && <Tag tone="positive" className="px-1.5 py-0 text-[10px] font-bold">LOWEST</Tag>}
                                  </div>
                                </div>
                              ))}
                            </div>
                            <div className="mt-2 text-right">
                              <p className="text-[12px] font-medium text-muted-foreground">TrueCost:</p>
                              <p className="tc-num text-[20px] font-bold leading-tight">{inr(hotel.trueCost)}<span className="text-[14px] font-medium text-muted-foreground">/night</span></p>
                              <p className="text-[11px] text-muted-foreground">incl. 18% taxes</p>
                            </div>
                          </div>
                        </div>

                        {/* Bottom Row */}
                        <div className="mt-6 pt-4 flex items-center justify-between border-t border-border/50">
                          <button className="flex items-center gap-2 text-[14px] font-semibold text-muted-foreground transition-colors hover:text-brand">
                            <Heart className="h-4 w-4" /> Save
                          </button>
                          <button className="flex items-center gap-2 rounded-xl bg-brand px-6 py-2.5 text-[14px] font-bold text-brand-foreground transition-all hover:bg-brand-strong hover:shadow-[var(--shadow-glow)]">
                            Book on {hotel.lowestPlatform} <ArrowRight className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </Panel>
                  </StaggerItem>
                ))}
              </Stagger>

              {/* Smart Filters (Below results) */}
              <div className="mt-8 flex flex-wrap justify-center gap-2">
                {smartFilters.map((f) => (
                  <Tag key={f} tone="neutral" className="cursor-pointer px-4 py-2 text-[14px] transition-colors hover:bg-surface-2 hover:text-brand">
                    {f}
                  </Tag>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </AppShell>
  );
}
