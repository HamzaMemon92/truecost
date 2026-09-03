export type SavedItem = {
  id: string; title: string; source_url?: string | null; provider?: string | null;
  price?: number | null; currency: string; metadata: Record<string, unknown>;
  created_at: string; updated_at: string;
};

export type PriceWatch = {
  id: string; title: string; target_price: number; current_price?: number | null;
  currency: string; source_url?: string | null; provider?: string | null;
  active: boolean; created_at: string; updated_at: string;
};

export type SavedCollectionItem = { id: string; note?: string | null; created_at: string; item: SavedItem };
export type SavedCollection = {
  id: string; name: string; description?: string | null; is_shared: boolean;
  share_token?: string | null; item_count: number; items: SavedCollectionItem[];
  created_at: string; updated_at: string;
};

export type Notice = {
  id: string; category: string; title: string; body: string; deep_link?: string | null;
  read_at?: string | null; created_at: string;
};
export type NotificationStats = { total: number; unread: number; categories: Record<string, number> };

export type Activity = {
  id: string; event_type: string; title: string; details: Record<string, unknown>; created_at: string;
};
export type ComparisonSummary = {
  id: string; query: string; category: string; provider_count: number; result_count: number;
  providers: string[]; created_at: string;
};
export type ComparisonObservation = {
  id: string; provider: string; product_id: string; product: Record<string, unknown>; observed_at: string;
};
export type ComparisonDetail = ComparisonSummary & { observations: ComparisonObservation[] };
export type ActivitySummary = {
  total_events: number; event_groups: Record<string, number>; comparison_count: number;
  recent_comparisons: ComparisonSummary[];
};
