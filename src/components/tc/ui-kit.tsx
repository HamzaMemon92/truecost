import { useEffect, useRef, useState, type ReactNode } from "react";
import { Info, Inbox } from "lucide-react";
import { motion, useInView } from "framer-motion";
import { cn } from "@/lib/utils";
import { ease, mountProps, riseIn, stagger } from "@/lib/motion";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Sparkline } from "@/components/tc/charts";

/* --------------------------------- Panel --------------------------------- */

type Elevation = "flat" | "card" | "raised" | "floating";

const elevationMap: Record<Elevation, string> = {
  flat: "shadow-none",
  card: "shadow-[var(--elev-card)]",
  raised: "shadow-[var(--elev-raised)]",
  floating: "shadow-[var(--elev-floating)]",
};

export function Panel({
  className,
  children,
  padded = true,
  elevation = "card",
  interactive = false,
  accent = false,
  glass = false,
}: {
  className?: string;
  children: ReactNode;
  padded?: boolean;
  elevation?: Elevation;
  interactive?: boolean;
  accent?: boolean;
  glass?: boolean;
}) {
  return (
    <section
      className={cn(
        "relative rounded-xl border border-border",
        glass ? "tc-glass" : "bg-card",
        elevationMap[elevation],
        interactive && "tc-lift",
        accent && "border-brand/30 shadow-[var(--shadow-glow)]",
        padded && "p-4 sm:p-5",
        className,
      )}
    >
      {accent && (
        <span
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand to-transparent"
        />
      )}
      {children}
    </section>
  );
}

/** Motion-aware panel that rises in when it enters the viewport. */
export function RevealPanel({
  delay = 0,
  className,
  children,
  ...rest
}: Parameters<typeof Panel>[0] & { delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ ...ease, delay }}
      className={cn("min-w-0", className)}
    >
      <Panel {...rest}>{children}</Panel>
    </motion.div>
  );
}

/** Stagger container for grids of cards. */
export function Stagger({
  children,
  className,
  delay,
  scroll = false,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
  scroll?: boolean;
}) {
  return (
    <motion.div
      variants={stagger(delay)}
      initial="hidden"
      {...(scroll
        ? { whileInView: "show", viewport: { once: true, margin: "-60px" } }
        : { animate: "show" })}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <motion.div variants={riseIn} className={cn("min-w-0", className)}>
      {children}
    </motion.div>
  );
}

export function PanelHeader({
  title,
  icon,
  action,
  hint,
  className,
}: {
  title: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
  hint?: string;
  className?: string;
}) {
  return (
    <header
      className={cn(
        "grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 sm:flex sm:justify-between",
        className,
      )}
    >
      <div className="flex min-w-0 items-center gap-2">
        {icon && (
          <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-brand-soft text-brand">
            {icon}
          </span>
        )}
        <h2 className="tc-panel-title truncate">{title}</h2>
        {hint && <InfoHint text={hint} />}
      </div>
      {action && <div className="shrink-0 text-sm">{action}</div>}
    </header>
  );
}

export function InfoHint({ text }: { text: string }) {
  return (
    <TooltipProvider delayDuration={120}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            aria-label={text}
            className="tc-ring shrink-0 rounded-full text-muted-foreground/70 transition-colors hover:text-brand"
          >
            <Info className="h-3.5 w-3.5" />
          </button>
        </TooltipTrigger>
        <TooltipContent className="max-w-[240px] text-xs leading-relaxed">
          {text}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/* --------------------------------- Chips --------------------------------- */

const toneMap = {
  brand: "bg-brand-soft text-brand-strong border-brand/15",
  positive: "bg-positive-soft text-positive border-positive/15",
  warning: "bg-warning-soft text-warning border-warning/20",
  danger: "bg-danger-soft text-danger border-danger/20",
  info: "bg-info-soft text-info border-info/15",
  neutral: "bg-muted text-muted-foreground border-border",
  gold: "bg-gold-soft text-gold-strong border-gold/40",
  solid: "bg-brand text-brand-foreground border-transparent",
} as const;

export type Tone = keyof typeof toneMap;

export function Tag({
  children,
  tone = "neutral",
  icon,
  className,
}: {
  children: ReactNode;
  tone?: Tone;
  icon?: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[11px] font-semibold tracking-tight",
        toneMap[tone],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  );
}

/* ------------------------------ Animated number --------------------------- */

export function AnimatedNumber({
  value,
  format,
  className,
  duration = 900,
}: {
  value: number;
  format?: (n: number) => string;
  className?: string;
  duration?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!inView) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setDisplay(value);
      return;
    }
    let raf = 0;
    const start = performance.now();
    const tick = (t: number) => {
      const p = Math.min((t - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(value * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, value, duration]);

  return (
    <span ref={ref} className={cn("tc-num", className)}>
      {format ? format(display) : Math.round(display).toLocaleString("en-IN")}
    </span>
  );
}

/* ------------------------------- Stat cards ------------------------------- */

// Sparkline data shapes for each stat card
const savingsSparkData = [
  { label: "1", value: 8200 }, { label: "2", value: 12400 }, { label: "3", value: 10800 },
  { label: "4", value: 16200 }, { label: "5", value: 14500 }, { label: "6", value: 22000 },
  { label: "7", value: 19800 }, { label: "8", value: 28000 }, { label: "9", value: 31240 },
];
const decisionsSparkData = [
  { label: "1", value: 28 }, { label: "2", value: 32 }, { label: "3", value: 30 },
  { label: "4", value: 35 }, { label: "5", value: 38 }, { label: "6", value: 36 },
  { label: "7", value: 40 }, { label: "8", value: 38 }, { label: "9", value: 42 },
];
const watchesSparkData = [
  { label: "1", value: 8 }, { label: "2", value: 10 }, { label: "3", value: 9 },
  { label: "4", value: 12 }, { label: "5", value: 11 }, { label: "6", value: 13 },
  { label: "7", value: 12 }, { label: "8", value: 15 }, { label: "9", value: 14 },
];
const co2SparkData = [
  { label: "1", value: 28 }, { label: "2", value: 32 }, { label: "3", value: 30 },
  { label: "4", value: 36 }, { label: "5", value: 38 }, { label: "6", value: 40 },
  { label: "7", value: 42 }, { label: "8", value: 44 }, { label: "9", value: 48.2 },
];

export const statSparklines = [savingsSparkData, decisionsSparkData, watchesSparkData, co2SparkData];

export function StatCard({
  label,
  value,
  sub,
  icon,
  iconBg = "bg-brand-soft text-brand",
  delta,
  deltaTone = "positive",
  sparkData,
  sparkTone = "brand",
  className,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode | undefined;
  icon?: ReactNode | undefined;
  iconBg?: string | undefined;
  delta?: string | undefined;
  deltaTone?: Tone | undefined;
  sparkData?: { label: string; value: number }[] | undefined;
  sparkTone?: "brand" | "danger" | "amber" | "positive" | "info" | undefined;
  className?: string | undefined;
}) {

  return (
    <div
      className={cn(
        "tc-card tc-lift group relative flex flex-col overflow-hidden",
        className,
      )}
    >
      <span
        aria-hidden
        className="pointer-events-none absolute -top-16 -right-12 h-32 w-32 rounded-full bg-brand/8 opacity-0 blur-2xl transition-opacity duration-300 group-hover:opacity-100"
      />
      {/* Top section: label + icon */}
      <div className="relative flex items-start justify-between gap-3 p-4 pb-2">
        <div className="min-w-0">
          <p className="text-[13px] font-medium text-muted-foreground">{label}</p>
          <p className="tc-num mt-1 truncate text-[23px] leading-tight font-bold text-foreground">
            {value}
          </p>
          {sub && <p className="mt-0.5 truncate text-xs text-muted-foreground">{sub}</p>}
        </div>
        <div className="relative flex shrink-0 flex-col items-end gap-2">
          {icon && (
            <span className={cn("grid h-9 w-9 place-items-center rounded-full transition-transform duration-300 group-hover:scale-105", iconBg)}>
              {icon}
            </span>
          )}
          {delta && <Tag tone={deltaTone}>{delta}</Tag>}
        </div>
      </div>
      {/* Bottom sparkline */}
      {sparkData && (
        <div className="mt-auto px-2 pb-1">
          <Sparkline data={sparkData} tone={sparkTone} />
        </div>
      )}
    </div>
  );
}

/* ------------------------------ Score display ----------------------------- */

export function ScoreRing({
  score,
  size = 64,
  label,
}: {
  score: number;
  size?: number;
  label?: string;
}) {
  const r = (size - 8) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.min(Math.max(score / 10, 0), 1);
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={5}
          className="stroke-border"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={5}
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          whileInView={{ strokeDashoffset: c * (1 - pct) }}
          viewport={{ once: true }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          className="stroke-brand"
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center">
        <span className="tc-num text-sm font-bold text-foreground">{score.toFixed(1)}</span>
        {label && <span className="text-[9px] text-muted-foreground">{label}</span>}
      </div>
    </div>
  );
}

export function FactorBar({
  label,
  value,
  suffix,
}: {
  label: string;
  value: number;
  suffix?: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 shrink-0 truncate text-xs text-muted-foreground">{label}</span>
      <span className="h-1.5 min-w-0 flex-1 overflow-hidden rounded-full bg-muted">
        <motion.span
          className="block h-full rounded-full bg-[image:var(--gradient-brand)]"
          initial={{ width: 0 }}
          whileInView={{ width: `${value}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        />
      </span>
      <span className="tc-num w-10 shrink-0 text-right text-xs font-semibold text-foreground">
        {suffix ?? `${value}%`}
      </span>
    </div>
  );
}

export function CheckList({ items, className }: { items: string[]; className?: string }) {
  return (
    <motion.ul variants={stagger(0.05)} {...mountProps} className={cn("space-y-2", className)}>
      {items.map((t) => (
        <motion.li
          key={t}
          variants={riseIn}
          className="flex items-start gap-2 text-[13px] text-foreground/85"
        >
          <CheckIcon />
          <span className="min-w-0">{t}</span>
        </motion.li>
      ))}
    </motion.ul>
  );
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 20 20" className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" fill="none">
      <path
        d="M4 10.5 8 14.5 16 5.5"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/* ----------------------------- Page structure ----------------------------- */

export function PageHeader({
  title,
  subtitle,
  actions,
  eyebrow,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  eyebrow?: ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={ease}
      className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-4 sm:flex sm:items-center sm:justify-between"
    >
      <div className="min-w-0">
        {eyebrow && <div className="mb-2">{eyebrow}</div>}
        <h1 className="tc-display text-[23px] leading-tight font-bold text-foreground sm:text-[28px]">
          {title}
        </h1>
        {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </motion.div>
  );
}

export function KeyValue({
  rows,
  emphasizeLast,
}: {
  rows: [string, ReactNode][];
  emphasizeLast?: boolean;
}) {
  return (
    <dl className="divide-y divide-border">
      {rows.map(([k, v], i) => {
        const last = emphasizeLast && i === rows.length - 1;
        return (
          <div key={k} className="flex items-center justify-between gap-4 py-2">
            <dt
              className={cn(
                "text-[13px] text-muted-foreground",
                last && "font-semibold text-foreground",
              )}
            >
              {k}
            </dt>
            <dd
              className={cn(
                "tc-num text-[13px] font-semibold text-foreground",
                last && "text-[15px] text-brand-strong",
              )}
            >
              {v}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}

/* -------------------------- States: empty / loading ------------------------ */

export function Skeleton({ className }: { className?: string }) {
  return <span className={cn("tc-shimmer block rounded-md", className)} />;
}

export function PanelSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <Panel>
      <Skeleton className="h-4 w-32" />
      <div className="mt-4 space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-9 w-9 rounded-full" />
            <Skeleton className="h-3 flex-1" />
            <Skeleton className="h-3 w-14" />
          </div>
        ))}
      </div>
    </Panel>
  );
}

export function EmptyState({
  title,
  body,
  icon,
  action,
  className,
}: {
  title: string;
  body?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-surface-2/60 px-6 py-12 text-center",
        className,
      )}
    >
      <span className="grid h-11 w-11 place-items-center rounded-full bg-brand-soft text-brand">
        {icon ?? <Inbox className="h-5 w-5" />}
      </span>
      <p className="tc-display mt-3 text-[15px] font-semibold text-foreground">{title}</p>
      {body && <p className="mt-1 max-w-sm text-[13px] text-muted-foreground">{body}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/* ------------------------------ Segmented control -------------------------- */

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className,
}: {
  options: readonly { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "inline-flex rounded-full border border-border bg-surface-2 p-0.5",
        className,
      )}
    >
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => onChange(o.value)}
            className={cn(
              "tc-ring relative rounded-full px-3 py-1.5 text-[12px] font-semibold transition-colors",
              active ? "text-brand-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {active && (
              <motion.span
                layoutId="tc-segment"
                transition={{ type: "spring", stiffness: 400, damping: 34 }}
                className="absolute inset-0 rounded-full bg-brand shadow-[var(--elev-card)]"
              />
            )}
            <span className="relative">{o.label}</span>
          </button>
        );
      })}
    </div>
  );
}

/* ─────────────────────────── DecisionScore ─────────────────────────── */

/**
 * Platform-wide DecisionScore badge.
 * Renders as a compact circular score indicator.
 * Click to expand the breakdown.
 */
export function DecisionScore({
  score,
  size = "md",
  showLabel = true,
  breakdown,
}: {
  score: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  breakdown?: { label: string; value: number }[];
}) {
  const [expanded, setExpanded] = useState(false);

  const defaultBreakdown = breakdown ?? [
    { label: "Price", value: score > 90 ? 95 : score > 80 ? 85 : 72 },
    { label: "Trust", value: score > 90 ? 92 : score > 80 ? 80 : 68 },
    { label: "Speed", value: score > 90 ? 90 : score > 80 ? 82 : 74 },
    { label: "Convenience", value: score > 90 ? 88 : score > 80 ? 78 : 65 },
  ];

  const sizeMap = {
    sm: { outer: "h-10 w-10", text: "text-[12px]", ring: 36, stroke: 3 },
    md: { outer: "h-12 w-12", text: "text-[13px]", ring: 44, stroke: 3.5 },
    lg: { outer: "h-16 w-16", text: "text-[17px]", ring: 60, stroke: 4 },
  };
  const s = sizeMap[size];
  const r = (s.ring - s.stroke * 2) / 2;
  const c = 2 * Math.PI * r;
  const pct = score / 100;
  const tone = score >= 90 ? "text-positive" : score >= 75 ? "text-brand" : "text-warning";

  return (
    <TooltipProvider delayDuration={80}>
      <Tooltip open={expanded} onOpenChange={setExpanded}>
        <TooltipTrigger asChild>
          <button
            type="button"
            className="group flex flex-col items-center gap-1 focus:outline-none"
            onClick={() => setExpanded((v) => !v)}
          >
            <div className={cn("relative", s.outer)}>
              <svg className="h-full w-full -rotate-90" viewBox={`0 0 ${s.ring} ${s.ring}`}>
                <circle cx={s.ring / 2} cy={s.ring / 2} r={r} fill="none" strokeWidth={s.stroke} className="stroke-muted" />
                <motion.circle
                  cx={s.ring / 2}
                  cy={s.ring / 2}
                  r={r}
                  fill="none"
                  strokeWidth={s.stroke}
                  strokeLinecap="round"
                  strokeDasharray={c}
                  initial={{ strokeDashoffset: c }}
                  whileInView={{ strokeDashoffset: c * (1 - pct) }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
                  className="stroke-brand"
                />
              </svg>
              <span className={cn("absolute inset-0 grid place-items-center tc-num font-bold", s.text, tone)}>
                {score}
              </span>
            </div>
            {showLabel && (
              <span className="text-[10px] font-semibold text-muted-foreground group-hover:text-brand transition-colors">
                Score
              </span>
            )}
          </button>
        </TooltipTrigger>
        <TooltipContent className="w-52 p-3" side="top">
          <p className="mb-2 text-[12px] font-bold text-foreground">DecisionScore breakdown</p>
          <div className="space-y-2">
            {defaultBreakdown.map((b) => (
              <div key={b.label} className="space-y-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-muted-foreground">{b.label}</span>
                  <span className="tc-num font-semibold">{b.value}</span>
                </div>
                <div className="h-1 overflow-hidden rounded-full bg-muted">
                  <div className="h-full rounded-full bg-brand" style={{ width: `${b.value}%` }} />
                </div>
              </div>
            ))}
          </div>
          <p className="mt-2 text-[10px] text-muted-foreground leading-relaxed">
            Weighted by your preferences: price, trust, speed, and convenience.
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/* ──────────────────────────── TrueCost ─────────────────────────────── */

/**
 * TrueCost component — clearly distinguishes list price from all-in cost.
 * Every comparison should use this instead of raw price display.
 */
export function TrueCost({
  listPrice,
  trueCost,
  breakdown,
  size = "md",
}: {
  listPrice: number;
  trueCost: number;
  size?: "sm" | "md" | "lg";
  breakdown?: { label: string; value: number; positive?: boolean }[];
}) {
  const savings = listPrice - trueCost;
  const isCheaper = trueCost < listPrice;

  const defaultBreakdown = breakdown ?? [
    { label: "Base price", value: listPrice },
    { label: "Delivery fee", value: Math.round(listPrice * 0.04) },
    { label: "Platform fee", value: Math.round(listPrice * 0.02) },
    { label: "Taxes", value: Math.round(listPrice * 0.03) },
    ...(isCheaper ? [{ label: "Discount applied", value: -Math.abs(savings - Math.round(listPrice * 0.09)), positive: true }] : []),
  ];

  const textSizeMap = { sm: "text-[13px]", md: "text-[16px]", lg: "text-[22px]" };
  const subSizeMap  = { sm: "text-[11px]", md: "text-[12px]", lg: "text-[14px]" };

  return (
    <TooltipProvider delayDuration={80}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button type="button" className="group text-left focus:outline-none">
            <div className="flex items-baseline gap-2">
              <span className={cn("tc-num font-bold text-foreground", textSizeMap[size])}>
                ₹{trueCost.toLocaleString("en-IN")}
              </span>
              {isCheaper && (
                <span className={cn("tc-num text-muted-foreground line-through", subSizeMap[size])}>
                  ₹{listPrice.toLocaleString("en-IN")}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={cn("text-[10px] font-semibold", isCheaper ? "text-positive" : "text-muted-foreground")}>
                TrueCost
              </span>
              {isCheaper && (
                <Tag tone="positive" className="text-[10px]">
                  Save ₹{Math.abs(savings).toLocaleString("en-IN")}
                </Tag>
              )}
              <Info className="h-3 w-3 text-muted-foreground/60 group-hover:text-brand transition-colors" />
            </div>
          </button>
        </TooltipTrigger>
        <TooltipContent className="w-56 p-3" side="top">
          <p className="mb-2 text-[12px] font-bold text-foreground">TrueCost breakdown</p>
          <div className="divide-y divide-border">
            {defaultBreakdown.map((b) => (
              <div key={b.label} className="flex items-center justify-between py-1.5 text-[11px]">
                <span className="text-muted-foreground">{b.label}</span>
                <span className={cn("tc-num font-semibold", b.positive ? "text-positive" : "text-foreground")}>
                  {b.value < 0 ? "−" : "+"}₹{Math.abs(b.value).toLocaleString("en-IN")}
                </span>
              </div>
            ))}
            <div className="flex items-center justify-between pt-2 text-[12px]">
              <span className="font-bold text-foreground">TrueCost</span>
              <span className="tc-num font-bold text-brand">₹{trueCost.toLocaleString("en-IN")}</span>
            </div>
          </div>
          <p className="mt-2 text-[10px] text-muted-foreground">
            Includes all fees, taxes, and applicable discounts.
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/* ─────────────────────── NexaSearching loading state ──────────────────── */

/**
 * Premium AI searching state — shows progressive step completion.
 */
export function NexaSearching({
  steps,
  currentStep,
}: {
  steps: string[];
  currentStep: number;
}) {
  return (
    <div className="space-y-2 rounded-xl border border-brand/20 bg-brand-soft/30 p-4">
      <p className="flex items-center gap-2 text-[12px] font-semibold text-brand">
        <motion.span
          animate={{ rotate: 360 }}
          transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
          className="inline-block"
        >
          ✦
        </motion.span>
        NEXA is searching…
      </p>
      <div className="space-y-1.5">
        {steps.map((step, i) => {
          const done = i < currentStep;
          const active = i === currentStep;
          return (
            <motion.div
              key={step}
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: done || active ? 1 : 0.35, x: 0 }}
              transition={{ delay: i * 0.12 }}
              className="flex items-center gap-2 text-[12px]"
            >
              <span className={cn(
                "grid h-4 w-4 shrink-0 place-items-center rounded-full text-[9px] font-bold",
                done ? "bg-positive text-white" : active ? "bg-brand text-white" : "bg-muted text-muted-foreground"
              )}>
                {done ? "✓" : active ? "●" : "○"}
              </span>
              <span className={cn(
                "font-medium",
                done ? "text-positive" : active ? "text-foreground" : "text-muted-foreground"
              )}>
                {step}
              </span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

/* ─────────────────────────── TrueCostBar ─────────────────────────── */
/**
 * TrueCost's signature component: visualizes exactly WHERE the total cost
 * comes from — base price, delivery, platform fee, taxes.
 *
 * Usage:
 *   <TrueCostBar base={249} delivery={30} fee={15} tax={5} />
 */
export function TrueCostBar({
  base,
  delivery = 0,
  fee = 0,
  tax = 0,
  className,
}: {
  base: number;
  delivery?: number;
  fee?: number;
  tax?: number;
  className?: string;
}) {
  const total = base + delivery + fee + tax;
  const pct = (n: number) => `${Math.round((n / total) * 100)}%`;

  const segments = [
    { label: "Base",     value: base,     color: "bg-brand",           textColor: "text-brand" },
    { label: "Delivery", value: delivery, color: "bg-sky-400",         textColor: "text-sky-600" },
    { label: "Fee",      value: fee,      color: "bg-amber-400",       textColor: "text-amber-600" },
    { label: "Tax",      value: tax,      color: "bg-muted-foreground/40", textColor: "text-muted-foreground" },
  ].filter((s) => s.value > 0);

  return (
    <div className={cn("space-y-2", className)}>
      {/* Proportional bar */}
      <div className="flex h-2 w-full overflow-hidden rounded-full">
        {segments.map((seg, i) => (
          <motion.div
            key={seg.label}
            initial={{ width: 0 }}
            animate={{ width: pct(seg.value) }}
            transition={{ duration: 0.6, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] }}
            className={cn("h-full", seg.color, i > 0 && "ml-px")}
          />
        ))}
      </div>

      {/* Labels */}
      <div className="flex flex-wrap gap-x-3 gap-y-1">
        {segments.map((seg) => (
          <span key={seg.label} className="flex items-center gap-1">
            <span className={cn("text-[10px] font-semibold", seg.textColor)}>
              {seg.label}
            </span>
            <span className="text-[10px] text-muted-foreground">
              ₹{seg.value}
            </span>
          </span>
        ))}
        <span className="ml-auto text-[10px] font-bold text-foreground">
          Total ₹{total}
        </span>
      </div>
    </div>
  );
}
