import { useState } from "react";
import { cn } from "@/lib/utils";

/**
 * Real provider / brand logos.
 * Resolved from each company's own domain via Google's public favicon service,
 * with a graceful monogram fallback when a logo can't be fetched.
 */
const DOMAINS: Record<string, string> = {
  // rides
  uber: "uber.com",
  "uber go": "uber.com",
  "uber xl": "uber.com",
  "uber premier": "uber.com",
  ola: "olacabs.com",
  "ola prime": "olacabs.com",
  rapido: "rapido.bike",
  "rapido cab": "rapido.bike",
  "namma yatri": "nammayatri.in",
  blusmart: "blu-smart.com",
  meru: "meru.in",

  // marketplaces & retail
  amazon: "amazon.in",
  flipkart: "flipkart.com",
  croma: "croma.com",
  "vijay sales": "vijaysales.com",
  "reliance digital": "reliancedigital.in",
  tatacliq: "tatacliq.com",
  myntra: "myntra.com",
  "hp online store": "hp.com",
  "dell store": "dell.com",
  "apple store": "apple.com",

  // grocery
  blinkit: "blinkit.com",
  zepto: "zeptonow.com",
  instamart: "swiggy.com",
  "swiggy instamart": "swiggy.com",
  swiggy: "swiggy.com",
  bigbasket: "bigbasket.com",
  more: "moreretail.in",
  dmart: "dmart.in",
  zomato: "zomato.com",
  jiomart: "jiomart.com",

  // brands
  apple: "apple.com",
  samsung: "samsung.com",
  sony: "sony.com",
  lg: "lg.com",
  dell: "dell.com",
  hp: "hp.com",
  lenovo: "lenovo.com",
  asus: "asus.com",
  philips: "philips.com",
  dyson: "dyson.com",
  bose: "bose.com",
  xiaomi: "mi.com",
  oneplus: "oneplus.in",

  // airlines & travel
  indigo: "goindigo.in",
  "air india": "airindia.com",
  vistara: "airvistara.com",
  spicejet: "spicejet.com",
  akasa: "akasaair.com",
  "akasa air": "akasaair.com",
  makemytrip: "makemytrip.com",
  goibibo: "goibibo.com",
  cleartrip: "cleartrip.com",
  "booking.com": "booking.com",
  airbnb: "airbnb.com",
  agoda: "agoda.com",
  taj: "tajhotels.com",
  "taj fort aguada resort": "tajhotels.com",
  "w goa, vagator": "marriott.com",
  "w goa": "marriott.com",
  marriott: "marriott.com",
  novotel: "accor.com",
  "novotel candolim": "accor.com",
  oyo: "oyorooms.com",
  "hotel prime ocean": "accor.com",

  // banks / payments / data partners
  icici: "icicibank.com",
  hdfc: "hdfcbank.com",
  sbi: "onlinesbi.sbi",
  visa: "visa.com",
  mastercard: "mastercard.com",
  stripe: "stripe.com",
  razorpay: "razorpay.com",
  shopify: "shopify.com",
  google: "google.com",
  "google cloud": "cloud.google.com",
  microsoft: "microsoft.com",
  paytm: "paytm.com",
  "amazon pay": "amazon.in",

  // grocery product brands
  amul: "amul.com",
  aashirvaad: "aashirvaad.com",
  fortune: "fortunefoods.com",
  "tata tea": "tataconsumer.com",
  "india gate": "indiagatefoods.com",
  "surf excel": "surfexcel.in",
  colgate: "colgate.com",
};

/** Best-effort lookup: exact match, then longest known key contained in the name. */
export function brandDomain(name: string): string | undefined {
  const key = name.trim().toLowerCase();
  if (DOMAINS[key]) return DOMAINS[key];
  const hit = Object.keys(DOMAINS)
    .filter((k) => key.includes(k))
    .sort((a, b) => b.length - a.length)[0];
  return hit ? DOMAINS[hit] : undefined;
}

const FORCE_MONOGRAM = new Set([
  "bigbasket.com",
  "moreretail.in",
  "amul.com",
  "aashirvaad.com",
  "fortunefoods.com",
  "tataconsumer.com",
  "indiagatefoods.com",
]);

function sourcesFor(domain: string) {
  if (FORCE_MONOGRAM.has(domain)) return [];
  return [
    `https://logo.clearbit.com/${domain}?size=128`,
    `https://unavatar.io/${domain}?fallback=false`,
    `https://icons.duckduckgo.com/ip3/${domain}.ico`,
    `https://www.google.com/s2/favicons?domain=${domain}&sz=256`,
    `https://${domain}/favicon.ico`,
  ];
}

/** Deterministic, pleasant tint for the monogram fallback. */
function tintFor(name: string) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) % 360;
  return h;
}

export function BrandLogo({
  name,
  size = 36,
  className,
  rounded = "rounded-[10px]",
}: {
  name: string;
  size?: number;
  className?: string;
  rounded?: string;
}) {
  const domain = brandDomain(name);
  const [idx, setIdx] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const sources = domain ? sourcesFor(domain) : [];
  const src = sources[idx];
  const initials = name
    .replace(/[^\p{L}\p{N} ]/gu, "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("");
  const hue = tintFor(name);

  return (
    <span
      title={name}
      className={cn(
        "relative grid shrink-0 place-items-center overflow-hidden border border-border bg-card shadow-[var(--elev-card)]",
        rounded,
        className,
      )}
      style={{ width: size, height: size }}
    >
      {/* Monogram sits underneath so a slow or failed logo never shows a blank tile. Fades out when loaded to prevent background bleed. */}
      <span
        aria-hidden={loaded}
        className={cn(
          "tc-display absolute inset-0 grid place-items-center font-bold transition-opacity duration-300",
          loaded ? "opacity-0" : "opacity-100"
        )}
        style={{
          background: `linear-gradient(140deg, oklch(0.94 0.045 ${hue}), oklch(0.88 0.06 ${hue}))`,
          color: `oklch(0.36 0.09 ${hue})`,
          fontSize: Math.max(9, Math.round(size * 0.38)),
          letterSpacing: "-0.02em",
        }}
      >
        {initials}
      </span>
      {src && (
        <img
          key={src}
          src={src}
          alt={`${name} logo`}
          width={size * 3}
          height={size * 3}
          loading="lazy"
          decoding="async"
          referrerPolicy="no-referrer"
          onLoad={(e) => {
            // Reject 1px tracking pixels / empty favicons and fall through.
            const el = e.currentTarget;
            if (el.naturalWidth < 12) setIdx((i) => i + 1);
            else setLoaded(true);
          }}
          onError={() => setIdx((i) => i + 1)}
          className={cn(
            "relative h-full w-full object-contain p-[6%] transition-opacity duration-200",
            loaded ? "opacity-100" : "opacity-0",
          )}
        />
      )}
    </span>
  );
}


/** Horizontal logo + label lockup used in tables and lists. */
export function BrandTag({
  name,
  label,
  sub,
  size = 36,
  className,
}: {
  name: string;
  label?: string;
  sub?: string;
  size?: number;
  className?: string;
}) {
  return (
    <span className={cn("flex min-w-0 items-center gap-2", className)}>
      <BrandLogo name={name} size={size} />
      <span className="min-w-0">
        <span className="block truncate text-[13px] font-semibold text-foreground">
          {label ?? name}
        </span>
        {sub && <span className="block truncate text-[11px] text-muted-foreground">{sub}</span>}
      </span>
    </span>
  );
}
