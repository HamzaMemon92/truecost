export type GroceryObjective = "cheapest" | "fastest" | "balanced";

export interface GroceryRequestPayload {
  items: string[];
  category: string;
  session_id: string;
  user_id: string;
  preferences: {
    objective: GroceryObjective;
  };
}

export interface GroceryItem {
  canonical_product_id: string;
  provider: string;
  provider_sku: string;
  title: string;
  brand: string;
  category: string;
  quantity_value: number;
  quantity_unit: string;
  price: number;
  currency: string;
  availability: string; // "In Stock" | "Out of Stock" | "Unknown"
  delivery_minutes: number | null;
  min_order_value: number;
  offers: string[];
  source_url: string;
  affiliate_url: string;
  source_type: string;
  provider_status: string;
  retrieved_at: string;
  expires_at: string;
  confidence: number;
}

export interface GroceryBasket {
  provider: string;
  items: GroceryItem[];
  missing_items: string[];
  subtotal: number;
  delivery_fee: number;
  final_total: number;
  estimated_delivery: string | null;
  delivery_minutes: number | null;
  is_complete: boolean;
}

export interface GroceryResponsePayload {
  items: string[];
  category: string;
  session_id: string;
  user_id: string;
  preferences: {
    objective: GroceryObjective;
  };
  complexity: string;
  route: string;
  agent_type: string | null;
  mcp_tools_used: any[];
  mcp_results: any[];
  evidence: string[];
  product_comparisons: any[];
  basket_results: GroceryBasket[];
  recommended_basket: GroceryBasket | null;
  alternative_baskets: GroceryBasket[];
  substitutions: any[];
  verification: string[];
  reasoning: string[];
  observability: Array<{
    provider_name: string;
    status: "success" | "timeout" | "error" | "no_results";
    latency_ms: number;
    error_class: string | null;
    item_count: number;
  }>;
}

const API_BASE_URL = "http://localhost:8000/api/v1";

export async function queryGrocery(
  items: string[],
  objective: GroceryObjective = "cheapest",
  signal?: AbortSignal
): Promise<GroceryResponsePayload> {
  const payload: GroceryRequestPayload = {
    items,
    category: "grocery",
    session_id: crypto.randomUUID(),
    user_id: "anonymous",
    preferences: {
      objective,
    },
  };

  const response = await fetch(`${API_BASE_URL}/grocery/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
    body: JSON.stringify(payload),
    signal: signal ?? null,
  });

  if (!response.ok) {
    let errorMsg = `API Error: ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMsg = typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch (e) {
      // Ignore JSON parse error if response is not JSON
    }
    throw new Error(errorMsg);
  }

  return response.json();
}
