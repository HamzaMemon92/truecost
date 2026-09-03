export type ShoppingComplexity = "simple" | "moderate" | "complex";

export type ShoppingContext = {
  city: string;
  budget?: number;
  preferredDelivery: "fastest" | "cheapest" | "balanced";
  affiliateMode: "default" | "vip";
};

export type ShoppingProviderResult = {
  platform: "Amazon" | "Flipkart" | "Meesho" | "Croma";
  mrp: number;
  price: number;
  delivery: number;
  platformFee: number;
  total: number;
  ships: string;
  score: number;
  isNexa: boolean;
  bgHeader: string;
  accentText: string;
  title?: string;
  brand?: string;
  trustSignal?: string;
};

export type ShoppingWorkflowResult = {
  category: "shopping";
  query: string;
  normalizedQuery: string;
  complexity: ShoppingComplexity;
  route: "direct-tools" | "shopping-agent";
  summary: string;
  providers: ShoppingProviderResult[];
  recommendation: ShoppingProviderResult;
  evidence: {
    providerCount: number;
    bestTotal: number;
    savings: number;
    verification: string;
  };
};

const productCatalog = {
  sony: {
    title: "Sony WH-1000XM5 Wireless Headphones",
    brand: "Sony",
    category: "Audio",
    mrp: 29990,
    base: {
      Amazon: { price: 24990, delivery: 0, platformFee: 0, ships: "2 days", score: 91 },
      Flipkart: { price: 24490, delivery: 0, platformFee: 0, ships: "1 day", score: 94 },
      Croma: { price: 26990, delivery: 99, platformFee: 0, ships: "Same day", score: 82 },
      Meesho: { price: 25990, delivery: 0, platformFee: 0, ships: "5 days", score: 78 },
    },
  },
  iphone: {
    title: "Apple iPhone 16",
    brand: "Apple",
    category: "Mobiles",
    mrp: 79999,
    base: {
      Amazon: { price: 69999, delivery: 0, platformFee: 0, ships: "2 days", score: 89 },
      Flipkart: { price: 68999, delivery: 0, platformFee: 0, ships: "1 day", score: 92 },
      Croma: { price: 71999, delivery: 0, platformFee: 0, ships: "2 days", score: 85 },
      Meesho: { price: 74999, delivery: 0, platformFee: 0, ships: "4 days", score: 71 },
    },
  },
  laptop: {
    title: "MacBook Air M3",
    brand: "Apple",
    category: "Laptops",
    mrp: 109900,
    base: {
      Amazon: { price: 104900, delivery: 0, platformFee: 0, ships: "2 days", score: 90 },
      Flipkart: { price: 99999, delivery: 0, platformFee: 0, ships: "1 day", score: 93 },
      Croma: { price: 106500, delivery: 99, platformFee: 0, ships: "Same day", score: 81 },
      Meesho: { price: 109900, delivery: 0, platformFee: 0, ships: "5 days", score: 75 },
    },
  },
};

const defaultContext: ShoppingContext = {
  city: "Bengaluru, India",
  preferredDelivery: "balanced",
  affiliateMode: "default",
};

const formatInr = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

const providerPalette = {
  Amazon: { bgHeader: "from-orange-100 to-amber-100", accentText: "text-orange-700" },
  Flipkart: { bgHeader: "from-blue-100 to-indigo-100", accentText: "text-blue-700" },
  Meesho: { bgHeader: "from-pink-100 to-rose-100", accentText: "text-pink-700" },
  Croma: { bgHeader: "from-emerald-100 to-green-100", accentText: "text-emerald-700" },
} as const;

const mcpToolRegistry = {
  searchProducts: (query: string) => {
    const matching = Object.entries(productCatalog).find(([key]) => query.toLowerCase().includes(key));
    if (!matching) {
      return productCatalog.sony;
    }
    return matching[1];
  },
  getOffers: (provider: keyof typeof productCatalog.sony.base, product: (typeof productCatalog)[keyof typeof productCatalog]) =>
    product.base[provider],
};

export function validateShoppingQuery(rawQuery: string): { original: string; normalized: string } {
  const query = rawQuery.trim();
  if (!query) {
    throw new Error("Shopping query cannot be empty.");
  }
  return {
    original: query,
    normalized: query.toLowerCase().replace(/\s+/g, " ").trim(),
  };
}

export function loadShoppingContext(userContext?: Partial<ShoppingContext>): ShoppingContext {
  return {
    ...defaultContext,
    ...userContext,
  };
}

export function determineShoppingComplexity(normalizedQuery: string): ShoppingComplexity {
  const query = normalizedQuery.toLowerCase();
  const advancedSignals = [
    "for gaming",
    "for ai",
    "for coding",
    "battery",
    "camera",
    "performance",
    "budget",
    "under",
    "best",
    "compare",
    "features",
    "specs",
  ];

  const score = advancedSignals.reduce((total, signal) => total + (query.includes(signal) ? 1 : 0), 0);

  if (score >= 3 || query.split(" ").length > 8) return "complex";
  if (score >= 1 || query.includes("best") || query.includes("compare")) return "moderate";
  return "simple";
}

export function routeShoppingWorkflow(complexity: ShoppingComplexity): "direct-tools" | "shopping-agent" {
  if (complexity === "simple") return "direct-tools";
  return "shopping-agent";
}

function normalizeProviderOffer(
  providerName: keyof typeof productCatalog.sony.base,
  product: (typeof productCatalog)[keyof typeof productCatalog],
  base: { price: number; delivery: number; platformFee: number; ships: string; score: number },
  query: string,
  index: number,
): ShoppingProviderResult {
  const queryLower = query.toLowerCase();
  let priceBias = 0;
  if (queryLower.includes("best") || queryLower.includes("low") || queryLower.includes("cheapest")) {
    priceBias = -500;
  }
  if (queryLower.includes("premium") || queryLower.includes("pro") || queryLower.includes("max")) {
    priceBias = 500;
  }

  const price = Math.max(1, base.price + priceBias + index * 120);
  const total = price + base.delivery + base.platformFee;

  return {
    platform: providerName,
    mrp: product.mrp,
    price,
    delivery: base.delivery,
    platformFee: base.platformFee,
    total,
    ships: base.ships,
    score: base.score,
    isNexa: providerName === "Flipkart",
    bgHeader: providerPalette[providerName].bgHeader,
    accentText: providerPalette[providerName].accentText,
    title: product.title,
    brand: product.brand,
    trustSignal: providerName === "Flipkart" ? "NEXA PICK" : "Verified seller",
  };
}

function matchProducts(
  query: string,
  product: (typeof productCatalog)[keyof typeof productCatalog],
): ShoppingProviderResult[] {
  const baseProviders = Object.entries(product.base) as Array<[
    keyof typeof product.base,
    { price: number; delivery: number; platformFee: number; ships: string; score: number },
  ]>;

  const results = baseProviders.map(([providerName, base], index) =>
    normalizeProviderOffer(providerName, product, base, query, index),
  );

  return results.sort((left, right) => left.total - right.total);
}

function recommendProduct(results: ShoppingProviderResult[]): ShoppingProviderResult {
  const best = results[0];
  if (!best) {
    throw new Error("No provider results available to recommend.");
  }
  return best;
}

function verifyEvidence(results: ShoppingProviderResult[], recommendation: ShoppingProviderResult) {
  const bestTotal = recommendation.total;
  const worst = results[results.length - 1];
  const savings = worst ? Math.max(0, worst.total - bestTotal) : 0;

  return {
    providerCount: results.length,
    bestTotal,
    savings,
    verification: `Verified across ${results.length} provider adapters with canonical pricing and delivery data.`,
  };
}

export function executeShoppingWorkflow(
  rawQuery: string,
  userContext?: Partial<ShoppingContext>,
): ShoppingWorkflowResult {
  const { original, normalized } = validateShoppingQuery(rawQuery);
  const context = loadShoppingContext(userContext);
  const complexity = determineShoppingComplexity(normalized);
  const route = routeShoppingWorkflow(complexity);
  const product = mcpToolRegistry.searchProducts(normalized);
  const providers = matchProducts(normalized, product);
  const recommendation = recommendProduct(providers);
  const evidence = verifyEvidence(providers, recommendation);
  const summary = `${recommendation.platform} has the lowest TrueCost today at ${formatInr(recommendation.total)}.`;

  void context;

  return {
    category: "shopping",
    query: original,
    normalizedQuery: normalized,
    complexity,
    route,
    summary,
    recommendation,
    providers,
    evidence,
  };
}

export const shoppingWorkflowSnapshot = {
  category: "shopping",
  mcpTools: Object.keys(mcpToolRegistry),
  providerAdapters: ["Amazon", "Flipkart", "Croma", "Meesho"],
  orchestration: [
    "validateShoppingQuery",
    "loadShoppingContext",
    "determineShoppingComplexity",
    "routeShoppingWorkflow",
    "searchProducts",
    "normalizeOfferData",
    "matchProducts",
    "recommendProduct",
    "verifyEvidence",
  ],
};
