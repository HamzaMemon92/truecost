import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { ArrowRight, Box, Car, Plane, Scale, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const chips = [
  { label: "Compare everything", icon: Scale, to: "/compare" as const },
  { label: "Find best deals", icon: Sparkles, to: "/compare" as const },
  { label: "Compare a product", icon: Car, to: "/compare/product" as const },
  { label: "Plan a trip", icon: Plane, to: "/travel" as const },
  { label: "Track a package", icon: Box, to: "/ownership" as const },
];

export function IntentInput({
  placeholder = "Compare products, services, and more…",
  className,
  size = "lg",
}: {
  placeholder?: string;
  className?: string;
  size?: "lg" | "md";
}) {
  const [value, setValue] = useState("");

  return (
    <div className={cn("w-full", className)}>
      <form
        onSubmit={(e) => e.preventDefault()}
        className={cn(
          "group grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 rounded-[24px] border border-border/50 bg-background/60 shadow-[var(--shadow-card)] backdrop-blur-2xl transition-all duration-300 hover:border-border focus-within:border-brand/50 focus-within:bg-background/80 focus-within:shadow-[0_0_40px_rgba(var(--color-brand-rgb),0.2)] dark:border-white/10 dark:bg-black/40 dark:shadow-[0_8px_32px_rgba(0,0,0,0.4)] dark:hover:border-white/20 dark:focus-within:bg-black/60",
          size === "lg" ? "px-4 py-3 sm:px-5 sm:py-3.5" : "px-3.5 py-2.5",
        )}
      >
        <span className="grid h-9 w-9 place-items-center rounded-full bg-muted text-brand transition-colors group-focus-within:bg-brand/10 group-focus-within:text-brand dark:bg-white/5">
          <Sparkles className="h-4 w-4" />
        </span>
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder}
          className={cn(
            "min-w-0 bg-transparent font-medium text-foreground placeholder:text-muted-foreground/60 focus:outline-none",
            size === "lg" ? "text-[16px]" : "text-[14px]",
          )}
        />
        <button
          type="submit"
          className="grid h-10 w-10 place-items-center rounded-full bg-brand text-brand-foreground shadow-[var(--shadow-glow)] transition-all hover:scale-105 hover:bg-brand-strong active:scale-95"
          aria-label="Ask agent"
        >
          <ArrowRight className="h-4.5 w-4.5" />
        </button>
      </form>

      <div className="no-scrollbar mt-5 flex gap-2.5 overflow-x-auto pb-1">
        {chips.map(({ label, icon: Icon, to }) => (
          <Link
            key={label}
            to={to}
            className="flex shrink-0 items-center gap-2 rounded-full border border-border/50 bg-muted/50 px-4 py-2 text-[13px] font-semibold text-muted-foreground transition-all hover:-translate-y-0.5 hover:border-border hover:bg-muted hover:text-foreground dark:border-white/10 dark:bg-white/5 dark:hover:border-white/20 dark:hover:bg-white/10"
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </Link>
        ))}
      </div>
    </div>
  );
}
