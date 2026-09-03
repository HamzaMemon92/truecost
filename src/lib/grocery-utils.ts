import { ShoppingBasket, Egg, Package, Coffee, Droplets, Apple, Fish, Carrot, Wheat } from "lucide-react";

// Represents a parsed item intent
export interface ParsedItem {
  qty: number;
  name: string;
}

// A simple dictionary to detect multiple common grocery items in a single string
// In a real app this would be a much larger NLP taxonomy
const COMMON_GROCERY_TOKENS = [
  "milk", "bread", "eggs", "butter", "cheese", "yogurt", "paneer",
  "sugar", "salt", "oil", "rice", "flour", "atta", "dal", "lentils",
  "tea", "coffee", "biscuit", "cookies", "chips", "namkeen",
  "apple", "banana", "onion", "potato", "tomato", "garlic", "ginger",
  "chicken", "fish", "meat", "surf", "soap", "shampoo", "toothpaste"
];

/**
 * Parses natural language input for multi-item intents.
 * e.g., "milk bread eggs" -> [{qty: 1, name: "milk"}, {qty: 1, name: "bread"}, {qty: 1, name: "eggs"}]
 * e.g., "2 milk, 1 bread" -> [{qty: 2, name: "milk"}, {qty: 1, name: "bread"}]
 */
export function parseMultiItemIntent(query: string): ParsedItem[] {
  const normalized = query.toLowerCase().trim();
  if (!normalized) return [];

  // Look for pattern: <number> <item>
  const qtyPattern = /(\d+)\s+([a-zA-Z\s]+)/g;
  const items: ParsedItem[] = [];
  let match;
  
  // If we find comma/and separated lists with quantities
  if (normalized.includes(",") || normalized.includes(" and ") || qtyPattern.test(normalized)) {
    // Reset regex index
    qtyPattern.lastIndex = 0;
    
    // Split by commas or "and"
    const parts = normalized.split(/,|\band\b/).map(s => s.trim()).filter(Boolean);
    
    for (const part of parts) {
      const qMatch = part.match(/^(\d+)\s+(.+)$/);
      if (qMatch && qMatch[1] && qMatch[2]) {
        items.push({ qty: parseInt(qMatch[1], 10), name: qMatch[2].trim() });
      } else {
        items.push({ qty: 1, name: part });
      }
    }
    
    if (items.length > 1) return items;
  }

  // Fallback: check if the user just typed space-separated known tokens "milk bread eggs"
  const tokens = normalized.split(/\s+/);
  const matchedTokens = tokens.filter(t => COMMON_GROCERY_TOKENS.includes(t));
  
  // Only auto-split if almost all tokens match known grocery items to avoid splitting "amul taaza milk"
  if (matchedTokens.length >= 2 && matchedTokens.length === tokens.length) {
    return matchedTokens.map(t => ({ qty: 1, name: t }));
  }

  return [];
}

// --------------------------------------------------------
// Autocomplete Data & Types
// --------------------------------------------------------

export type SuggestionType = "PRODUCT" | "BRAND" | "CATEGORY" | "RECENT" | "POPULAR" | "SMART";

export interface AutocompleteSuggestion {
  id: string;
  type: SuggestionType;
  title: string;
  subtitle?: string;
  icon?: any;
}

const CATALOG: AutocompleteSuggestion[] = [
  { id: "s-1", type: "PRODUCT", title: "Amul Taaza Toned Milk 1L", subtitle: "Milk · Dairy" },
  { id: "s-2", type: "PRODUCT", title: "Amul Gold Full Cream Milk 1L", subtitle: "Milk · Dairy" },
  { id: "s-3", type: "PRODUCT", title: "Nandini GoodLife Toned Milk 500ml", subtitle: "Milk · Dairy" },
  { id: "s-4", type: "PRODUCT", title: "Britannia White Bread", subtitle: "Bread · Bakery" },
  { id: "s-5", type: "PRODUCT", title: "Harvest Gold Brown Bread", subtitle: "Bread · Bakery" },
  { id: "s-6", type: "PRODUCT", title: "Farm Fresh White Eggs 6 pcs", subtitle: "Eggs · Dairy" },
  { id: "s-7", type: "PRODUCT", title: "Fortune Sunlite Refined Sunflower Oil 1L", subtitle: "Oil · Pantry" },
  { id: "s-8", type: "PRODUCT", title: "Madhur Pure & Hygienic Sugar 1kg", subtitle: "Sugar · Pantry" },
  { id: "s-9", type: "PRODUCT", title: "Tata Salt Vacuum Evaporated 1kg", subtitle: "Salt · Pantry" },
  { id: "s-10", type: "PRODUCT", title: "Surf Excel Easy Wash Detergent Powder 1kg", subtitle: "Detergent · Household" },
  { id: "s-11", type: "PRODUCT", title: "Aashirvaad Shudh Chakki Atta 5kg", subtitle: "Flour · Pantry" },
  { id: "s-12", type: "PRODUCT", title: "Nescafe Classic Instant Coffee 50g", subtitle: "Coffee · Beverages" },
  { id: "s-13", type: "PRODUCT", title: "Brooke Bond Red Label Tea 500g", subtitle: "Tea · Beverages" },
  
  { id: "b-1", type: "BRAND", title: "Amul", subtitle: "Dairy products" },
  { id: "b-2", type: "BRAND", title: "Britannia", subtitle: "Bakery & Biscuits" },
  { id: "b-3", type: "BRAND", title: "Tata", subtitle: "Pantry staples" },
  
  { id: "c-1", type: "CATEGORY", title: "Milk & Dairy", icon: Droplets },
  { id: "c-2", type: "CATEGORY", title: "Fresh Fruits", icon: Apple },
  { id: "c-3", type: "CATEGORY", title: "Fresh Vegetables", icon: Carrot },
  { id: "c-4", type: "CATEGORY", title: "Meat & Seafood", icon: Fish },
  { id: "c-5", type: "CATEGORY", title: "Atta, Rice & Dal", icon: Wheat },
];

const RECENT_SEARCHES: AutocompleteSuggestion[] = [
  { id: "r-1", type: "RECENT", title: "Amul Milk 1L" },
  { id: "r-2", type: "RECENT", title: "Nescafe 50g" },
];

const POPULAR_SEARCHES: AutocompleteSuggestion[] = [
  { id: "p-1", type: "POPULAR", title: "Farm Eggs 12 pcs" },
  { id: "p-2", type: "POPULAR", title: "Britannia Bread" },
];

/**
 * Super fast, deterministic local search simulator for autocomplete.
 */
export async function fetchAutocomplete(query: string): Promise<AutocompleteSuggestion[]> {
  // Simulate network delay
  await new Promise(r => setTimeout(r, 100));
  
  const normalized = query.toLowerCase().trim();
  
  if (!normalized) {
    return [
      ...RECENT_SEARCHES,
      ...POPULAR_SEARCHES,
    ];
  }

  // Rank 1: Exact prefix match on title
  const prefixMatches = CATALOG.filter(c => c.title.toLowerCase().startsWith(normalized));
  
  // Rank 2: Token match (e.g. "amul milk" matches "Amul Taaza Toned Milk")
  const tokens = normalized.split(/\s+/);
  const tokenMatches = CATALOG.filter(c => 
    !prefixMatches.includes(c) && 
    tokens.every(t => c.title.toLowerCase().includes(t) || (c.subtitle && c.subtitle.toLowerCase().includes(t)))
  );

  const results = [...prefixMatches, ...tokenMatches];
  
  // If we have some matches, maybe add a smart suggestion
  if (normalized.includes("milk") || normalized.includes("bread") || normalized.includes("egg")) {
    results.push({ id: "sm-1", type: "SMART", title: "Breakfast essentials", subtitle: "Quick add bundle" });
  }

  return results.slice(0, 8); // Max 8 results to keep UI calm
}
