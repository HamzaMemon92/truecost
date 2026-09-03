import { publicApi } from './client';

export interface FlightSearchRequest {
  origin: string;
  destination: string;
  departure_date: string;
  return_date?: string;
  passengers: number;
  cabin_class: 'economy' | 'business' | 'first';
  trip_type: 'one_way' | 'round_trip';
  flexible_dates?: boolean;
}

export interface FlightOption {
  provider: string;
  flight_number: string;
  origin: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  duration_minutes: number;
  stops: number;
  cabin_class: string;
  base_fare: number;
  taxes_fees: number;
  total_fare: number;
  per_passenger_fare: number;
  baggage_included: string;
  cancellation_policy: string;
  deep_link: string;
  data_source: string;
  authoritative?: boolean;
  freshness_state?: 'verified' | 'preview' | 'stale' | 'unavailable';
  source_freshness?: string;
}

export interface FlightSearchResult {
  search_id: string;
  origin: string;
  destination: string;
  departure_date: string;
  passengers: number;
  cabin_class: string;
  options: FlightOption[];
  cheapest_option: FlightOption | null;
  recommendation_reason: string;
  generated_at: string;
  disclaimer: string;
}

export interface HotelSearchRequest {
  destination: string;
  checkin_date: string;
  checkout_date: string;
  guests: number;
  rooms: number;
  budget_max?: number;
  star_rating_min?: number;
}

export interface HotelOption {
  provider: string;
  hotel_name: string;
  star_rating: number;
  location: string;
  price_per_night: number;
  total_price: number;
  taxes_fees: number;
  cancellation_policy: string;
  breakfast_included: boolean;
  amenities: string[];
  deep_link: string;
  data_source: string;
  authoritative?: boolean;
  freshness_state?: 'verified' | 'preview' | 'stale' | 'unavailable';
  source_freshness?: string;
}

export interface HotelSearchResult {
  search_id: string;
  destination: string;
  checkin_date: string;
  checkout_date: string;
  nights: number;
  guests: number;
  options: HotelOption[];
  best_value_option: HotelOption | null;
  recommendation_reason: string;
  generated_at: string;
  disclaimer: string;
}

export interface PopularRoute { origin: string; origin_city: string; destination: string; destination_city: string }
export interface Airport { code: string; name: string }

export async function searchFlights(req: FlightSearchRequest): Promise<FlightSearchResult> {
  return publicApi<FlightSearchResult>('/travel/flights/search', { method: 'POST', body: JSON.stringify(req) });
}

export async function searchAirports(q: string): Promise<Airport[]> {
  const data = await publicApi<{ airports: Airport[] }>(`/travel/flights/airports?q=${encodeURIComponent(q)}`);
  return data.airports;
}

export async function getPopularRoutes(): Promise<PopularRoute[]> {
  const data = await publicApi<{ routes: PopularRoute[] }>('/travel/flights/popular-routes');
  return data.routes;
}

export async function searchHotels(req: HotelSearchRequest): Promise<HotelSearchResult> {
  return publicApi<HotelSearchResult>('/travel/hotels/search', { method: 'POST', body: JSON.stringify(req) });
}
