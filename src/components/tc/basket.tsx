import React, { useEffect, useState } from "react";
import { X, Plus, Minus, ShoppingCart, Trash2, Truck, AlertTriangle } from "lucide-react";
import { BasketItem } from "@/lib/use-basket";
import { inr } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

interface FulfillmentGroup {
  provider: string;
  items: any[];
  subtotal: number;
  delivery_fee: number;
  platform_fee: number;
  discount: number;
  coupon_discount: number;
  final_total: number;
  estimated_delivery: string | null;
  missing_items: string[];
  deep_link_type?: string;
  deep_link_url?: string;
}

interface BasketComparisonResult {
  mode: string;
  total: number;
  savings: number;
  retailer_count: number;
  deliveries: number;
  fulfillment_groups: FulfillmentGroup[];
  unavailable_items: string[];
  explanations: string[];
}

interface BasketDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  items: BasketItem[];
  location: string;
  updateQuantity: (id: string, qty: number) => void;
  removeItem: (id: string) => void;
}

export function BasketDrawer({
  isOpen,
  onClose,
  items,
  location,
  updateQuantity,
  removeItem
}: BasketDrawerProps) {
  const [mode, setMode] = useState<string>("CHEAPEST");
  const [evaluation, setEvaluation] = useState<BasketComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || items.length === 0) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetch("http://127.0.0.1:8000/api/v1/grocery/basket/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        items: items.map(i => ({ canonical_product_id: i.canonical_product_id, quantity: i.quantity })),
        location: { city: location },
        mode
      })
    })
      .then(res => {
        if (!res.ok) throw new Error("Failed to evaluate basket");
        return res.json();
      })
      .then(data => {
        if (isMounted) {
          // data is list of options, we just take the top one for the current mode
          if (Array.isArray(data) && data.length > 0) {
            setEvaluation(data[0]);
          } else {
            setEvaluation(null);
            setError("No fulfillment options found for these items in your area.");
          }
        }
      })
      .catch(err => {
        console.error("Basket eval error", err);
        if (isMounted) {
          setEvaluation(null);
          setError("We couldn't calculate the best deal right now. Please try again.");
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [items, location, mode, isOpen]);

  // Handle slide over classes
  const panelClasses = cn(
    "fixed inset-y-0 right-0 z-50 w-full md:w-[450px] bg-background shadow-2xl transform transition-transform duration-300 ease-in-out flex flex-col border-l border-border",
    isOpen ? "translate-x-0" : "translate-x-full"
  );

  const backdropClasses = cn(
    "fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity duration-300",
    isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
  );

  return (
    <>
      <div className={backdropClasses} onClick={onClose} />
      <div className={panelClasses}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <ShoppingCart className="w-5 h-5 text-brand" />
            <h2 className="text-xl font-bold tracking-tight">TrueCost Basket</h2>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-surface-2 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {items.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground space-y-4">
              <ShoppingCart className="w-16 h-16 opacity-20" />
              <p>Your basket is empty</p>
            </div>
          ) : (
            <>
              {/* Mode Selector */}
              <div className="bg-surface-2 p-1 rounded-xl flex items-center w-full">
                {["CHEAPEST", "FASTEST", "SINGLE_RETAILER"].map(m => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    className={cn(
                      "flex-1 py-1.5 text-xs font-bold rounded-lg capitalize transition-colors",
                      mode === m ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {m.replace('_', ' ').toLowerCase()}
                  </button>
                ))}
              </div>

              {/* Items List */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider">
                  Requested Items ({items.reduce((s, i) => s + i.quantity, 0)})
                </h3>
                {items.map(item => (
                  <div key={item.canonical_product_id} className="flex gap-4 p-3 bg-surface border border-border rounded-xl">
                    <div className="w-16 h-16 bg-white rounded-lg border border-border flex items-center justify-center p-2 shrink-0">
                      {item.image_url ? (
                        <img src={item.image_url} alt={item.title} className="max-w-full max-h-full object-contain" />
                      ) : (
                        <ShoppingCart className="w-6 h-6 text-muted-foreground opacity-20" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0 flex flex-col justify-between">
                      <div className="flex justify-between items-start gap-2">
                        <p className="font-bold text-sm leading-tight text-foreground line-clamp-2">{item.title}</p>
                        <button onClick={() => removeItem(item.canonical_product_id)} className="p-1 text-muted-foreground hover:text-destructive">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="flex items-center gap-3 mt-2">
                        <div className="flex items-center gap-2 bg-surface-2 rounded-lg p-1 border border-border">
                          <button 
                            onClick={() => updateQuantity(item.canonical_product_id, item.quantity - 1)}
                            className="w-6 h-6 flex items-center justify-center bg-background rounded-md shadow-sm"
                          >
                            <Minus className="w-3 h-3" />
                          </button>
                          <span className="text-sm font-bold w-4 text-center">{item.quantity}</span>
                          <button 
                            onClick={() => updateQuantity(item.canonical_product_id, item.quantity + 1)}
                            className="w-6 h-6 flex items-center justify-center bg-background rounded-md shadow-sm"
                          >
                            <Plus className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Fulfillment Plan */}
              {loading ? (
                <div className="animate-pulse space-y-4 pt-4 border-t border-border">
                  <div className="h-4 bg-surface-3 rounded w-1/3"></div>
                  <div className="h-24 bg-surface-2 rounded-xl"></div>
                </div>
              ) : evaluation ? (
                <div className="space-y-4 pt-4 border-t border-border">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider">
                      Optimal Fulfillment Plan
                    </h3>
                    {evaluation.savings > 0 && (
                      <span className="bg-green-500/20 text-green-500 text-xs font-bold px-2 py-1 rounded-md">
                        Save {inr(evaluation.savings)}
                      </span>
                    )}
                  </div>
                  
                  {evaluation.unavailable_items.length > 0 && (
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3">
                      <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-bold text-red-500">Some items unavailable</p>
                        <p className="text-xs text-red-500/80">{evaluation.unavailable_items.length} items cannot be fulfilled in this area.</p>
                      </div>
                    </div>
                  )}

                  {evaluation.fulfillment_groups.map((fg, idx) => (
                    <div key={idx} className="p-4 bg-surface border border-border rounded-xl space-y-3 relative overflow-hidden">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-black text-foreground capitalize">{fg.provider}</p>
                          <div className="flex items-center gap-1 text-xs text-brand font-bold mt-1">
                            <Truck className="w-3 h-3" />
                            {fg.estimated_delivery}
                          </div>
                        </div>
                        <p className="font-bold">{inr(fg.final_total)}</p>
                      </div>
                      
                      <div className="text-xs text-muted-foreground space-y-1 pt-2 border-t border-border/50">
                        <div className="flex justify-between">
                          <span>Items ({fg.items.reduce((s,i) => s + (i.quantity_value || 1), 0)})</span>
                          <span>{inr(fg.subtotal)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Delivery</span>
                          <span>{fg.delivery_fee > 0 ? inr(fg.delivery_fee) : 'Free'}</span>
                        </div>
                        {fg.platform_fee > 0 && (
                          <div className="flex justify-between">
                            <span>Platform fee</span>
                            <span>{inr(fg.platform_fee)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : error ? (
                <div className="space-y-4 pt-4 border-t border-border">
                  <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-bold text-red-500">Evaluation Failed</p>
                      <p className="text-xs text-red-500/80">{error}</p>
                    </div>
                  </div>
                </div>
              ) : null}
            </>
          )}
        </div>

        {/* Footer Checkout */}
        {items.length > 0 && evaluation && (
          <div className="p-4 border-t border-border bg-surface-2 flex flex-col gap-4">
            <div className="flex justify-between items-end">
              <div>
                <p className="text-sm text-muted-foreground">TrueCost Total</p>
                <p className="text-2xl font-black text-foreground">{inr(evaluation.total)}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-muted-foreground">Via {evaluation.deliveries} deliveries</p>
              </div>
            </div>
            
            <div className="space-y-3">
              {evaluation.fulfillment_groups.map((fg, idx) => {
                const isSingle = evaluation.fulfillment_groups.length === 1;
                const itemCount = fg.items.reduce((s,i) => s + (i.quantity_value || 1), 0);
                return (
                  <div key={idx} className={cn("flex flex-col gap-2", !isSingle && "p-3 bg-surface border border-border rounded-xl")}>
                    {!isSingle && (
                      <div className="flex justify-between items-center text-sm font-bold">
                        <span className="capitalize">{fg.provider}</span>
                        <span className="text-muted-foreground font-normal">{itemCount} items</span>
                      </div>
                    )}
                    {fg.deep_link_url ? (
                      <a 
                        href={fg.deep_link_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full py-3.5 bg-brand hover:bg-brand-strong text-brand-foreground font-black rounded-xl transition-transform active:scale-[0.98] shadow-lg shadow-brand/20 text-center flex items-center justify-center gap-2"
                      >
                        {isSingle ? `Continue to ${fg.provider}` : `Open ${fg.provider}`}
                      </a>
                    ) : (
                      <button disabled className="w-full py-3.5 bg-surface-3 text-muted-foreground font-bold rounded-xl text-center">
                        Link Unavailable
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
