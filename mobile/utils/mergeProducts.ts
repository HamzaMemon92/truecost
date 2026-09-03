import { ProductProps, ProviderPrice } from '../components/ProductCard';

/**
 * TrueCost Product Merge Engine
 *
 * Takes a stream of products arriving from multiple providers
 * and merges them into canonical product cards with side-by-side pricing.
 *
 * Example:
 *   Input:  [{ name: "Amul Milk 1L", provider: "Zepto", price: 68 },
 *             { name: "Amul Milk 1ltr", provider: "Blinkit", price: 72 }]
 *   Output: [{ name: "Amul Milk 1L", prices: [Zepto ₹68 BEST, Blinkit ₹72] }]
 */

// --- String Normalization ---

function normalize(name: string): string {
  return name
    .toLowerCase()
    .replace(/\d+\s*(ml|l|kg|g|gm|ltr|litre|pack|pcs|pieces?|units?)\b/gi, '') // strip weight/volume
    .replace(/[^\w\s]/g, '') // strip punctuation
    .replace(/\s+/g, ' ')
    .trim();
}

// Dice coefficient — fast, accurate fuzzy matching for product names
function similarity(a: string, b: string): number {
  const na = normalize(a);
  const nb = normalize(b);
  if (na === nb) return 1.0;
  if (na.length < 2 || nb.length < 2) return 0.0;

  const getBigrams = (str: string): Map<string, number> => {
    const bigrams = new Map<string, number>();
    for (let i = 0; i < str.length - 1; i++) {
      const bigram = str.slice(i, i + 2);
      bigrams.set(bigram, (bigrams.get(bigram) ?? 0) + 1);
    }
    return bigrams;
  };

  const aBigrams = getBigrams(na);
  const bBigrams = getBigrams(nb);
  let intersectionSize = 0;

  for (const [bigram, count] of aBigrams) {
    const bCount = bBigrams.get(bigram) ?? 0;
    intersectionSize += Math.min(count, bCount);
  }

  return (2.0 * intersectionSize) / (na.length - 1 + (nb.length - 1));
}

// --- Main Merge Function ---

const MERGE_THRESHOLD = 0.72;

function getPrice(p: any): number {
  return p.price ?? 0;
}

export function mergeProducts(
  existing: ProductProps[],
  incoming: ProductProps[]
): ProductProps[] {
  // Clone existing array to avoid mutation
  const merged: ProductProps[] = existing.map(p => ({
    ...p,
    prices: [...p.prices],
  }));

  for (const product of incoming) {
    let bestMatch: ProductProps | null = null;
    let bestScore = 0;

    for (const canonical of merged) {
      const score = similarity(product.name, canonical.name);
      if (score >= MERGE_THRESHOLD && score > bestScore) {
        bestScore = score;
        bestMatch = canonical;
      }
    }

    if (bestMatch) {
      // Merge: add new provider prices into the existing canonical card
      const existingProviders = new Set(bestMatch.prices.map(p => p.provider));
      for (const price of product.prices) {
        if (!existingProviders.has(price.provider)) {
          bestMatch.prices.push(price);
        }
      }
    } else {
      // New unique product — add to list
      merged.push({ ...product, prices: [...product.prices] });
    }
  }

  // Re-rank: mark cheapest price as isBest across all merged prices
  return merged.map(product => {
    const minPrice = Math.min(...product.prices.map(getPrice));
    return {
      ...product,
      prices: [...product.prices]
        .map(p => ({ ...p, isBest: getPrice(p) === minPrice }))
        .sort((a, b) => getPrice(a) - getPrice(b)),
    };
  });
}

// --- Savings Calculator ---

export function calculateSavings(products: ProductProps[]): number {
  return products.reduce((total, product) => {
    if (product.prices.length < 2) return total;
    const prices = product.prices.map(getPrice);
    const cheapest = Math.min(...prices);
    const mostExpensive = Math.max(...prices);
    return total + (mostExpensive - cheapest);
  }, 0);
}
export let sessionSavedTotal = 0;
export const sessionRecents: string[] = [];
