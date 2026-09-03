import { publicApi } from './client';

export interface RideRequest {
  pickup_lat: number;
  pickup_lng: number;
  drop_lat: number;
  drop_lng: number;
  ride_class?: 'standard' | 'premium' | 'auto' | 'bike';
  objective?: 'cheapest' | 'fastest' | 'balanced';
}

export interface ProviderFare {
  provider: string;
  ride_class: string;
  base_fare: number;
  distance_fare: number;
  time_fare: number;
  surge_multiplier: number;
  platform_fee: number;
  total_fare: number;
  eta_minutes: number;
  is_available: boolean;
  deep_link: string;
  is_surge: boolean;
  promo_available: boolean;
  promo_code?: string;
  promo_savings: number;
}

export interface MobilityComparisonResult {
  request_id: string;
  pickup_lat: number;
  pickup_lng: number;
  drop_lat: number;
  drop_lng: number;
  estimated_distance_km: number;
  estimated_duration_minutes: number;
  provider_fares: ProviderFare[];
  recommended_provider: string;
  recommendation_reason: string;
  truecost_winner: ProviderFare;
  objective: string;
  generated_at: string;
  data_source: string;
}

export interface MobilityProvider {
  id: string;
  name: string;
  classes: string[];
  logo: string;
}

export async function compareMobilityFares(req: RideRequest): Promise<MobilityComparisonResult> {
  return publicApi<MobilityComparisonResult>('/mobility/compare', { method: 'POST', body: JSON.stringify(req) });
}

export async function getMobilityProviders(): Promise<{ providers: MobilityProvider[]; disclaimer: string }> {
  return publicApi('/mobility/providers');
}
