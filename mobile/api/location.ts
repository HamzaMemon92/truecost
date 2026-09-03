import { BACKEND_URL } from '../config';

export interface ServiceabilityRequest {
  lat?: number;
  lng?: number;
  pincode?: string;
  city?: string;
}

export interface ProviderServiceability {
  provider: string;
  category: string;
  is_serviceable: boolean;
  estimated_delivery?: string;
  reason?: string;
}

export interface ServiceabilityResult {
  location_label: string;
  pincode?: string;
  city?: string;
  is_any_serviceable: boolean;
  providers: ProviderServiceability[];
  generated_at: string;
  disclaimer: string;
}

export interface PopularCity {
  name: string;
  pincode: string;
  lat: number;
  lng: number;
}

export async function checkServiceability(
  req: ServiceabilityRequest
): Promise<ServiceabilityResult> {
  const res = await fetch(`${BACKEND_URL}/api/v1/location/serviceability`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error('Serviceability check failed');
  return res.json();
}

export async function getPopularCities(): Promise<PopularCity[]> {
  const res = await fetch(`${BACKEND_URL}/api/v1/location/popular-cities`);
  if (!res.ok) throw new Error('Failed to load cities');
  const data = await res.json();
  return data.cities;
}
