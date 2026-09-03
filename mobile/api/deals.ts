import { publicApi } from './client';

export interface Deal {
  id: string;
  title: string;
  provider: string;
  category: string;
  discount_pct?: number;
  cashback_pct?: number;
  cashback_amount?: number;
  min_order?: number;
  max_cashback?: number;
  valid_until?: string;
  payment_method?: string;
  deep_link: string;
  terms: string;
  is_expiring_soon: boolean;
  data_source: string;
}

export interface DealsResponse {
  deals: Deal[];
  total: number;
  generated_at: string;
  disclaimer: string;
}

export async function getDeals(category?: string): Promise<DealsResponse> {
  const query = category ? `?category=${encodeURIComponent(category)}` : '';
  return publicApi<DealsResponse>(`/deals${query}`);
}
