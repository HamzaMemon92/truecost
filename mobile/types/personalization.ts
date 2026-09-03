export type NotificationPreferences = { price_drops?: boolean; travel_alerts?: boolean; savings_updates?: boolean; deals?: boolean; account_updates?: boolean };
export type AccessibilityPreferences = { reduced_motion?: boolean; larger_text?: boolean; high_contrast?: boolean; screen_reader_hints?: boolean };
export type PrivacyPreferences = { personalized_recommendations?: boolean; retain_activity?: boolean; save_location_history?: boolean; product_analytics?: boolean };
export type ProfilePreferences = {
  objective?: 'cheapest' | 'balanced' | 'fastest'; delivery_preference?: 'cheapest' | 'balanced' | 'fastest';
  preferred_categories?: string[]; preferred_providers?: string[]; dietary?: string[];
  notification_preferences?: NotificationPreferences; accessibility?: AccessibilityPreferences; privacy?: PrivacyPreferences;
  language?: string; region?: string; currency?: string; monthly_budget?: number | null;
};
export type Profile = { user_id: string; email: string | null; phone_number?: string | null; display_name?: string | null; preferences: ProfilePreferences & Record<string, unknown> };
export type SavedAddress = { id: string; label: string; address_line: string; locality?: string | null; city: string; state?: string | null; postal_code: string; country_code: string; latitude: number; longitude: number; is_default: boolean; created_at: string; updated_at: string };
export type Serviceability = { address_id: string; category?: string | null; status: 'verification_required'; can_request_comparison: boolean; checked_providers: string[]; message: string };
export type PaymentType = 'card' | 'upi' | 'wallet' | 'net_banking';
export type PaymentPreference = { id: string; method_type: PaymentType; label: string; issuer?: string | null; network?: string | null; last4?: string | null; masked_identifier?: string | null; benefit_tags: string[]; is_preferred: boolean; created_at: string; updated_at: string };
export type CategoryMetadata = { id: string; name: string; engine_category: string; capability: string; providers: string[]; availability_verified: false };
