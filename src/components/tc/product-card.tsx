import { useState } from "react";
import { cn } from "@/lib/utils";
import { Clock, Info, Check, Image as ImageIcon, Egg } from "lucide-react";
import { inr } from "@/lib/mock-data";

import { resolveProductImage } from "@/lib/image-resolution";

function CategoryIcon({ category, className }: { category: string, className?: string }) {
  if (category.toLowerCase().includes("dairy") || category.toLowerCase().includes("milk")) {
    return <ImageIcon className={className} />; // Or a custom milk icon
  }
  if (category.toLowerCase().includes("egg")) {
    return <Egg className={className} />;
  }
  if (category.toLowerCase().includes("bakery") || category.toLowerCase().includes("bread")) {
    return <ImageIcon className={className} />; // Or a bread icon
  }
  return <ImageIcon className={className} />;
}

export function ProductCard({ comparison, onAdd }: { comparison: any, onAdd?: (resolvedImageUrl: string | null) => void }) {
  const { product, offers, winners, analysis } = comparison;
  const [expanded, setExpanded] = useState(false);
  
  // Sort offers by effective price
  const sortedOffers = [...offers].sort((a, b) => {
    const aPrice = analysis[a.provider]?.effective_price || a.price;
    const bPrice = analysis[b.provider]?.effective_price || b.price;
    return aPrice - bPrice;
  });

  const bestOffer = sortedOffers.find(o => o.provider === winners.cheapest) || sortedOffers[0];
  const bestAnalysis = analysis[bestOffer?.provider];

  const resolvedImage = resolveProductImage(product, bestOffer);

  return (
    <div className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition-all hover:shadow-md">
      <div className="flex flex-col sm:flex-row">
        {/* Product Image & Core Info */}
        <div className="flex sm:w-1/3 flex-col items-center justify-center bg-surface-2 p-6 sm:border-r border-border relative">
          {resolvedImage.url ? (
            <img 
              src={resolvedImage.url} 
              alt={product.title}
              className="h-32 w-32 object-contain mix-blend-multiply"
              loading="lazy"
            />
          ) : (
            <div className="flex h-32 w-32 items-center justify-center rounded-xl bg-surface-3 border border-border/50">
              <CategoryIcon category={product.category} className="h-10 w-10 text-muted-foreground opacity-50" />
            </div>
          )}
          {resolvedImage.confidence === "TRUSTED" && (
            <div className="absolute top-2 left-2 bg-green-500/10 text-green-600 text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded flex items-center gap-1">
              <Check className="w-2.5 h-2.5" /> Verified
            </div>
          )}
        </div>
        
        {/* Details & Best Deal */}
        <div className="flex flex-1 flex-col justify-between p-5 sm:p-6">
          <div className="space-y-1">
            <span className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
              {product.brand}
            </span>
            <h3 className="text-lg font-black leading-tight text-foreground">
              {product.title}
            </h3>
            <div className="flex gap-2 text-sm text-muted-foreground font-medium pt-1">
              <span>{product.normalized_quantity} {product.normalized_unit}</span>
              {product.pack_count > 1 && <span>• {product.pack_count} Pack</span>}
              {product.tags && product.tags.length > 0 && (
                <span className="capitalize">• {product.tags[0]}</span>
              )}
            </div>
          </div>
          
          <div className="mt-6 flex flex-wrap items-end justify-between gap-4 border-t border-border/50 pt-5">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <p className="text-[11px] font-semibold uppercase text-brand tracking-wider">Best Deal: {bestOffer.provider}</p>
                {bestOffer.source_type === "mock" && (
                  <span className="text-[9px] font-bold uppercase bg-yellow-500/20 text-yellow-600 px-1.5 py-0.5 rounded border border-yellow-500/30">Mock</span>
                )}
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black tc-num text-foreground">
                  {inr(bestAnalysis?.effective_price || bestOffer.price)}
                </span>
                {bestOffer.mrp && bestOffer.mrp > (bestAnalysis?.effective_price || bestOffer.price) && (
                  <span className="text-sm font-medium text-muted-foreground line-through tc-num">
                    {inr(bestOffer.mrp)}
                  </span>
                )}
                <span className="text-xs font-semibold text-muted-foreground ml-1 bg-surface-2 px-1.5 py-0.5 rounded">
                  {bestAnalysis?.unit_price}
                </span>
              </div>
              <div className="flex items-center gap-3 mt-2 text-xs font-medium text-muted-foreground">
                <span className="flex items-center gap-1 text-positive">
                  <Check className="h-3.5 w-3.5" /> {bestOffer.availability === "IN_STOCK" ? "In Stock" : "Low Stock"}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" /> {bestOffer.delivery_minutes} min
                </span>
              </div>
            </div>
            
            <div className="flex flex-col gap-2 w-full sm:w-auto">
              <button 
                onClick={() => setExpanded(!expanded)}
                className="text-[13px] font-semibold text-muted-foreground hover:text-foreground text-center"
              >
                {expanded ? "Hide comparison" : `Compare ${offers.length} offers`}
              </button>
              <button 
                onClick={() => onAdd?.(resolvedImage.url)}
                className="rounded-xl bg-brand px-6 py-3 text-sm font-bold text-brand-foreground shadow-[var(--shadow-glow)] hover:bg-brand-strong transition-transform active:scale-95 w-full sm:w-auto"
              >
                Add to basket
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Expanded Comparison */}
      {expanded && (
        <div className="border-t border-border bg-surface-1 p-5 sm:p-6">
          <h4 className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground mb-4">Retailer Comparison</h4>
          <div className="space-y-3">
            {sortedOffers.map(offer => {
              const offerAnalysis = analysis[offer.provider];
              const isBest = offer.provider === bestOffer.provider;
              const isUnavailable = ["OUT_OF_STOCK", "UNAVAILABLE_IN_AREA"].includes(offer.availability);
              
              return (
                <div 
                  key={offer.provider} 
                  className={cn(
                    "flex flex-wrap items-center justify-between gap-4 rounded-xl border p-4 transition-colors",
                    isBest ? "border-brand/30 bg-brand-soft/20" : "border-border bg-card",
                    isUnavailable && "opacity-60"
                  )}
                >
                  <div className="flex-1 min-w-[120px]">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[15px]">{offer.provider}</span>
                      {offer.provider === winners.fastest && (
                        <span className="rounded bg-teal-500/10 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">Fastest</span>
                      )}
                    </div>
                    {isUnavailable ? (
                      <p className="text-xs font-semibold text-danger mt-1 uppercase">{offer.availability.replace(/_/g, " ")}</p>
                    ) : (
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1">
                        <Clock className="h-3 w-3" /> {offer.delivery_minutes} min ETA
                      </div>
                    )}
                  </div>
                  
                  <div className="flex flex-col items-end min-w-[100px]">
                    <div className="flex items-center gap-1.5">
                      <span className={cn(
                        "text-lg font-black tc-num",
                        isBest ? "text-brand" : "text-foreground"
                      )}>
                        {inr(offerAnalysis?.effective_price || offer.price)}
                      </span>
                    </div>
                    {offerAnalysis?.breakdown?.delivery_fee > 0 ? (
                      <span className="text-[11px] text-muted-foreground">
                        + {inr(offerAnalysis.breakdown.delivery_fee)} delivery
                      </span>
                    ) : !isUnavailable && (
                      <span className="text-[11px] font-semibold text-positive">
                        Free delivery
                      </span>
                    )}
                  </div>
                  
                  {offer.deep_link_url ? (
                    <a 
                      href={offer.deep_link_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full sm:w-auto rounded-lg border border-border bg-brand text-brand-foreground px-4 py-2 text-sm font-semibold text-center transition-colors hover:bg-brand-strong disabled:opacity-50 inline-block"
                    >
                      Get Deal
                    </a>
                  ) : (
                    <button 
                      disabled={true}
                      className="w-full sm:w-auto rounded-lg border border-border bg-surface-2 px-4 py-2 text-sm font-semibold text-foreground transition-colors disabled:opacity-50"
                    >
                      {isUnavailable ? "Unavailable" : "Link Unavailable"}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
