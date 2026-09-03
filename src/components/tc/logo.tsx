import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  return (
    <div className={cn("relative shrink-0 flex items-center justify-center", className)}>
      <img 
        src="/truecost-logo.png" 
        alt="TrueCost Icon" 
        className="absolute h-full w-full object-contain"
      />
    </div>
  );
}

export function Logo({
  size = "md",
  className,
  showWordmark = true,
  tagline = true,
}: {
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  showWordmark?: boolean;
  tagline?: boolean;
}) {
  if (!showWordmark) {
    const iconMap = {
      sm: "h-6 w-8",
      md: "h-10 w-[54px]",
      lg: "h-12 w-[64px]",
      xl: "h-16 w-[80px]",
    };
    return <LogoMark className={cn(iconMap[size], className)} />;
  }

  const fullMap = {
    sm: "w-28", // 112px
    md: "w-[180px]", // 180px - perfect for sidebar
    lg: "w-[220px]", // 220px
    xl: "w-[280px]", // 280px
  };

  return (
    <div className={cn("relative shrink-0 flex items-center justify-start", fullMap[size], className)}>
      <img 
        src="/truecost-logo-full.png" 
        alt="TrueCost Logo" 
        className="h-auto w-full object-contain object-left"
      />
    </div>
  );
}
