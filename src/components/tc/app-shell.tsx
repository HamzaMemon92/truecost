import { useEffect, useState, type ReactNode } from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import {
  Bell,
  Car,
  ChevronLeft,
  ChevronRight,
  Eye,
  Hotel,
  LayoutGrid,
  Menu,
  MoreHorizontal,
  PiggyBank,
  Plane,
  Scale,
  ShieldCheck,
  ShoppingBag,
  ShoppingBasket,
  Sparkles,
  RotateCcw,
  Tag,
  TrendingDown,
  UtensilsCrossed,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Logo } from "./logo";
import { ThemeToggle } from "./theme-toggle";
import { CommandBar } from "./command-bar";
import { user } from "@/lib/mock-data";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

/* ─── Nav config ─── */
const navGroups = [
  {
    label: "Decide",
    items: [
      { to: "/dashboard", label: "Dashboard", sub: "Overview", icon: LayoutGrid },
      { to: "/ask", label: "Ask TrueCost", sub: "AI assistant", icon: Sparkles },
      { to: "/compare", label: "Compare", sub: "Everything", icon: Scale },
      { to: "/compare/rides", label: "Rides", sub: "Find best ride", icon: Car },
      { to: "/grocery", label: "Grocery", sub: "Smart savings", icon: ShoppingBasket },
      { to: "/food", label: "Food", sub: "Order smarter", icon: UtensilsCrossed },
      { to: "/travel", label: "Travel", sub: "Flights & stays", icon: Plane },
      { to: "/hotels", label: "Hotels", sub: "Best rates", icon: Hotel },
      { to: "/deals", label: "Deals", sub: "AI opportunities", icon: Tag },
      { to: "/shopping", label: "More", sub: "Explore all", icon: MoreHorizontal },
    ],
  },
  {
    label: "Own & Track",
    items: [
      { to: "/activity", label: "Orders & Trips", sub: "Your activity", icon: ShieldCheck },
      { to: "/watchlist", label: "Price Watch", sub: "Track prices", icon: Eye },
      { to: "/savings", label: "Savings", sub: "Your savings", icon: PiggyBank },
      { to: "/ownership", label: "Ownership", sub: "What you own", icon: RotateCcw },
    ],
  },
] as const;

const mobileNav = [
  { to: "/dashboard", label: "Home", icon: LayoutGrid },
  { to: "/compare", label: "Compare", icon: Scale },
  { to: "/ask", label: "Ask", icon: Sparkles },
  { to: "/activity", label: "Activity", icon: ShieldCheck },
  { to: "/savings", label: "Savings", icon: PiggyBank },
] as const;

/* ─── Helpers ─── */
function useIsActive() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (to: string) => {
    // Dashboard and Compare hub: exact match only
    if (to === "/dashboard" || to === "/compare") {
      return pathname === to || pathname === to + "/";
    }
    // All other routes: exact match or child routes
    return pathname === to || pathname.startsWith(to + "/");
  };
}

/* ─── Collapsed icon-only nav list ─── */
function NavListCollapsed({ onNavigate }: { onNavigate?: (() => void) | undefined }) {
  const isActive = useIsActive();
  return (
    <TooltipProvider delayDuration={100}>
      <div className="space-y-1">
        {(navGroups as readonly { label: string; items: readonly { to: string; label: string; sub: string; icon: React.FC<any> }[] }[]).flatMap((g) => g.items).map(({ to, label, icon: Icon }) => {
          const active = isActive(to);
          return (
            <Tooltip key={`${to}-${label}`}>
              <TooltipTrigger asChild>
                <Link
                  to={to}
                  onClick={onNavigate}
                  className={cn(
                    "tc-ring relative flex h-10 w-10 items-center justify-center rounded-xl transition-colors mx-auto",
                    active
                      ? "bg-brand text-brand-foreground shadow-[var(--shadow-glow)]"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  {active && (
                    <motion.span
                      layoutId="tc-nav-active-collapsed"
                      transition={{ type: "spring", stiffness: 420, damping: 36 }}
                      className="absolute inset-0 rounded-xl bg-brand shadow-[var(--shadow-glow)]"
                    />
                  )}
                  <Icon className="relative h-4 w-4" strokeWidth={2.2} />
                </Link>
              </TooltipTrigger>
              <TooltipContent side="right" className="text-[12px] font-semibold">
                {label}
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
    </TooltipProvider>
  );
}

/* ─── Expanded nav list ─── */
function NavList({ onNavigate }: { onNavigate?: (() => void) | undefined }) {
  const isActive = useIsActive();
  return (
    <div className="space-y-5">
      {navGroups.map((group) => (
        <div key={group.label}>
          <p className="mb-1.5 px-3 text-[10px] font-semibold tracking-[0.18em] text-muted-foreground/60 uppercase">
            {group.label}
          </p>
          <nav className="space-y-0.5">
            {group.items.map(({ to, label, sub, icon: Icon }) => {
              const active = isActive(to);
              return (
                <Link
                  key={`${to}-${label}`}
                  to={to}
                  onClick={onNavigate}
                  className={cn(
                    "tc-ring group relative flex items-center gap-3 rounded-xl px-2.5 py-2 text-[13px] font-medium transition-colors",
                    active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {active && (
                    <motion.span
                      layoutId={`tc-nav-active-${label}`}
                      transition={{ type: "spring", stiffness: 420, damping: 36 }}
                      className="absolute inset-0 rounded-xl border border-brand/20 bg-gradient-to-r from-brand-soft to-transparent shadow-[var(--elev-card)]"
                    />
                  )}
                  {active && (
                    <span className="absolute top-2.5 bottom-2.5 -left-2 w-[3px] rounded-full bg-brand shadow-[0_0_12px_var(--brand)]" />
                  )}
                  <span
                    className={cn(
                      "relative grid h-7 w-7 shrink-0 place-items-center rounded-lg transition-colors",
                      active
                        ? "bg-brand text-brand-foreground shadow-[var(--shadow-glow)]"
                        : "bg-surface-2 text-muted-foreground group-hover:bg-muted group-hover:text-foreground",
                    )}
                  >
                    <Icon className="h-3.5 w-3.5" strokeWidth={2.2} />
                  </span>
                  <span className="relative min-w-0 flex-1">
                    <span className="block truncate leading-tight">{label}</span>
                    {sub && (
                      <span className="block truncate text-[10px] font-normal text-muted-foreground/70 leading-tight mt-0.5">
                        {sub}
                      </span>
                    )}
                  </span>
                  <ChevronRight
                    className={cn(
                      "relative ml-auto h-3.5 w-3.5 shrink-0 transition-all",
                      active
                        ? "text-brand opacity-100"
                        : "-translate-x-1 opacity-0 group-hover:translate-x-0 group-hover:opacity-60",
                    )}
                  />
                </Link>
              );
            })}
          </nav>
        </div>
      ))}
    </div>
  );
}

/* ─── Mobile bottom tab bar ─── */
function MobileBottomNav() {
  const isActive = useIsActive();
  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-border bg-background/90 backdrop-blur-xl safe-area-pb">
      <div className="flex items-stretch justify-around px-1 py-1.5">
        {mobileNav.map(({ to, label, icon: Icon }) => {
          const active = isActive(to);
          return (
            <Link
              key={to}
              to={to}
              className="relative flex flex-1 flex-col items-center gap-1 rounded-xl py-2 text-[10px] font-semibold transition-colors"
            >
              {active && (
                <motion.span
                  layoutId="mobile-nav-indicator"
                  transition={{ type: "spring", stiffness: 420, damping: 36 }}
                  className="absolute inset-0 rounded-xl bg-brand-soft/50"
                />
              )}
              <Icon
                className={cn(
                  "relative h-5 w-5 transition-colors",
                  active ? "text-brand" : "text-muted-foreground"
                )}
                strokeWidth={active ? 2.5 : 2}
              />
              <span className={cn("relative", active ? "text-brand" : "text-muted-foreground")}>
                {label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}


function SavingsSparkline() {
  const pts = [3, 5, 4, 7, 5, 8, 6, 9, 7, 10, 9, 11];
  const max = Math.max(...pts);
  const w = 100;
  const h = 32;
  const path = pts
    .map((v, i) => {
      const x = (i / (pts.length - 1)) * w;
      const y = h - (v / max) * h;
      return `${i === 0 ? "M" : "L"}${x},${y}`;
    })
    .join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ height: 32 }} preserveAspectRatio="none">
      <defs>
        <linearGradient id="savSpark" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--color-brand)" stopOpacity="0.35" />
          <stop offset="100%" stopColor="var(--color-brand)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${path} L${w},${h} L0,${h} Z`} fill="url(#savSpark)" />
      <path d={path} fill="none" stroke="var(--color-brand)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ─── Desktop Sidebar Body (expanded) ─── */
function SidebarBody({
  onNavigate,
  onCollapse,
}: {
  onNavigate?: (() => void) | undefined;
  onCollapse?: (() => void) | undefined;
}) {
  return (
    <div className="relative flex h-full flex-col gap-5 overflow-y-auto p-4 no-scrollbar">
      <span
        aria-hidden
        className="pointer-events-none absolute -top-24 -left-16 h-56 w-56 rounded-full bg-brand/10 blur-3xl"
      />

      {/* Logo + collapse button row */}
      <div className="relative flex items-center justify-between px-1 pt-1">
        <Link to="/" onClick={onNavigate}>
          <Logo size="md" tagline />
        </Link>
        {onCollapse && (
          <button
            onClick={onCollapse}
            title="Collapse sidebar"
            className="grid h-7 w-7 shrink-0 place-items-center rounded-lg text-muted-foreground/60 transition-colors hover:bg-muted hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      <div className="relative flex-1">
        <NavList onNavigate={onNavigate} />
      </div>

      {/* Savings card */}
      <div className="relative mt-auto space-y-3 pt-2">
        <div className="relative overflow-hidden rounded-2xl border border-brand/20 bg-gradient-to-br from-brand-soft via-brand-soft/60 to-transparent p-3.5">
          <span
            aria-hidden
            className="pointer-events-none absolute -top-8 -right-6 h-24 w-24 rounded-full bg-brand/15 blur-2xl"
          />
          <div className="relative flex items-center gap-1.5 text-brand-strong">
            <Sparkles className="h-3.5 w-3.5" />
            <span className="text-[11px] font-bold tracking-wide">Total verified savings</span>
          </div>
          <p className="tc-num tc-display relative mt-1.5 text-[24px] leading-none font-bold text-brand-strong">
            ₹31,240
          </p>
          <p className="relative mt-0.5 text-[11px] text-brand-strong/70">This month · 42 decisions</p>
          <div className="relative mt-2.5 overflow-hidden rounded-lg">
            <SavingsSparkline />
          </div>
        </div>

        {/* User card */}
        <div className="flex items-center gap-2.5 rounded-2xl border border-border bg-surface-2/60 p-2.5 transition-colors hover:border-brand/25">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br from-foreground to-foreground/75 text-[11px] font-bold text-background">
            {user.initials}
          </span>
          <span className="min-w-0 flex-1">
            <span className="flex items-center gap-1">
              <span className="block truncate text-[13px] font-semibold">{user.name}</span>
              <span className="text-base">👑</span>
            </span>
            <span className="block truncate text-[11px] text-muted-foreground">
              {user.plan} plan
            </span>
          </span>
          <ThemeToggle />
        </div>
      </div>
    </div>
  );
}

/* ─── Desktop Sidebar Collapsed strip ─── */
function SidebarCollapsed({ onExpand }: { onExpand: () => void }) {
  return (
    <div className="flex h-full flex-col items-center gap-3 py-4 no-scrollbar overflow-y-auto">
      {/* Logo icon only */}
      <Link to="/" className="mb-1">
        <Logo showWordmark={false} size="sm" />
      </Link>

      {/* Expand button */}
      <button
        onClick={onExpand}
        title="Expand sidebar"
        className="grid h-9 w-9 place-items-center rounded-xl border border-border bg-surface-2/80 text-muted-foreground transition-all hover:border-brand/30 hover:bg-brand-soft/40 hover:text-brand"
      >
        <ChevronRight className="h-4 w-4" />
      </button>

      <div className="my-1 h-px w-8 bg-border" />

      {/* Icon-only nav */}
      <NavListCollapsed />
    </div>
  );
}

/* ─── Page transition wrapper ─── */
function PageTransition({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={pathname}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -4 }}
        transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

/* ─── EXPANDED sidebar width ─── */
const SIDEBAR_EXPANDED = 272; // px  (17rem)
const SIDEBAR_COLLAPSED = 64; // px  (4rem)

/* ═══════════════════════ AppShell ═══════════════════════ */
export function AppShell({
  children,
}: {
  children: ReactNode;
}) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  // Auto-collapse sidebar when navigating to /ask
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  useEffect(() => {
    if (pathname === "/ask") {
      setCollapsed(true);
    }
    // Do NOT auto-expand when leaving /ask — let user control it
  }, [pathname]);

  const sidebarWidth = collapsed ? SIDEBAR_COLLAPSED : SIDEBAR_EXPANDED;

  return (
    <div className="min-h-screen w-full bg-background">

      {/* ── Desktop Sidebar (animates width) ── */}
      <motion.aside
        animate={{ width: sidebarWidth }}
        transition={{ type: "spring", stiffness: 320, damping: 32 }}
        className="fixed inset-y-0 left-0 z-30 hidden border-r border-sidebar-border bg-sidebar overflow-hidden lg:block"
      >
        <AnimatePresence mode="wait" initial={false}>
          {collapsed ? (
            <motion.div
              key="collapsed"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="h-full w-16"
            >
              <SidebarCollapsed onExpand={() => setCollapsed(false)} />
            </motion.div>
          ) : (
            <motion.div
              key="expanded"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="h-full"
              style={{ width: SIDEBAR_EXPANDED }}
            >
              <SidebarBody onCollapse={() => setCollapsed(true)} />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.aside>

      {/* ── Mobile Drawer (slide-in overlay) ── */}
      <AnimatePresence>
        {drawerOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <motion.button
              aria-label="Close menu"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-foreground/40 backdrop-blur-[3px]"
              onClick={() => setDrawerOpen(false)}
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", stiffness: 380, damping: 36 }}
              className="absolute inset-y-0 left-0 w-[17rem] border-r border-sidebar-border bg-sidebar shadow-[var(--elev-floating)]"
            >
              <button
                aria-label="Close menu"
                onClick={() => setDrawerOpen(false)}
                className="absolute top-4 right-3 z-10 rounded-md p-1 text-muted-foreground hover:bg-muted"
              >
                <X className="h-4 w-4" />
              </button>
              <SidebarBody onNavigate={() => setDrawerOpen(false)} />
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── Main content (animates left padding to match sidebar) ── */}
      <motion.div
        animate={{ paddingLeft: sidebarWidth }}
        transition={{ type: "spring", stiffness: 320, damping: 32 }}
        className="hidden lg:block"
      >
        {/* Top header */}
        <header className="sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur-xl">
          <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-3 px-4 sm:px-6">
            {/* ⌘+K Command Bar */}
            <div className="min-w-0 flex-1">
              <CommandBar />
            </div>

            {/* Right actions */}
            <div className="ml-auto flex shrink-0 items-center gap-1.5">
              <Link
                to="/savings"
                className="hidden items-center gap-1.5 rounded-full border border-brand/20 bg-brand-soft px-3 py-1.5 text-xs font-semibold text-brand-strong transition-colors hover:border-brand/40 md:flex"
              >
                <ShoppingBag className="h-3.5 w-3.5" />
                <span className="tc-num">₹31,240 saved</span>
              </Link>
              <button
                aria-label="Notifications"
                className="relative rounded-full p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <Bell className="h-4 w-4" />
                <span className="absolute top-1.5 right-2 h-1.5 w-1.5 rounded-full bg-danger" />
              </button>
              <span className="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-br from-foreground to-foreground/75 text-[11px] font-bold text-background">
                {user.initials}
              </span>
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1400px] px-4 pt-5 pb-6 sm:px-6">
          <PageTransition>{children}</PageTransition>
        </main>

        {/* Footer */}
        <footer className="border-t border-border bg-surface-2/60">
          <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-4 py-2.5 sm:px-6">
            <p className="text-[11px] text-muted-foreground/70">
              © 2025 TrueCost. AI Consumer Agent.
            </p>
            <div className="hidden items-center gap-5 sm:flex">
              {[
                { icon: TrendingDown, label: "Better prices" },
                { icon: Sparkles,    label: "Smarter choices" },
                { icon: Scale,       label: "All in one place" },
                { icon: ShieldCheck, label: "Powered by AI" },
              ].map(({ icon: Ico, label }) => (
                <span key={label} className="flex items-center gap-1.5 text-[11px] text-muted-foreground/60">
                  <Ico className="h-3 w-3" />
                  <span>{label}</span>
                </span>
              ))}
            </div>
          </div>
        </footer>
      </motion.div>

      {/* ── Mobile layout (unchanged) ── */}
      <div className="lg:hidden">
        {/* Mobile top bar */}
        <header className="sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur-xl">
          <div className="flex h-14 items-center gap-3 px-4">
            <button
              aria-label="Open menu"
              onClick={() => setDrawerOpen(true)}
              className="-ml-1 rounded-md p-2 text-muted-foreground hover:bg-muted"
            >
              <Menu className="h-4.5 w-4.5" />
            </button>
            <Link to="/">
              <Logo showWordmark={false} size="sm" />
            </Link>
            <div className="ml-auto flex items-center gap-1.5">
              <button className="relative rounded-full p-2 text-muted-foreground">
                <Bell className="h-4 w-4" />
                <span className="absolute top-1.5 right-2 h-1.5 w-1.5 rounded-full bg-danger" />
              </button>
              <span className="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-br from-foreground to-foreground/75 text-[11px] font-bold text-background">
                {user.initials}
              </span>
            </div>
          </div>
        </header>

        <main className="px-4 pt-5 pb-24 sm:px-6">
          <PageTransition>{children}</PageTransition>
        </main>

        {/* Mobile bottom nav — proper active state */}
        <MobileBottomNav />
      </div>
    </div>
  );
}
