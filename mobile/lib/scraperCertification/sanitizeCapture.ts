export type ScraperExecutionMode = 'REAL_LIVE_SCRAPE' | 'REAL_CAPTURE_REPLAY' | 'SYNTHETIC_MUTATION' | 'MOCK';

export const CertificationProviderRegistry: Record<string, string[]> = {
  grocery: ['blinkit', 'zepto', 'swiggy_instamart', 'bigbasket', 'swiggy'],
  shopping: ['amazon', 'flipkart', 'meesho', 'myntra'],
  mobility: ['nammayatri', 'ola', 'rapido', 'uber'],
  flights: ['cleartrip', 'goibibo', 'ixigo', 'makemytrip'],
  hotels: ['cleartrip', 'goibibo', 'ixigo', 'makemytrip'],
  finance: ['bankbazaar', 'creditmantri', 'paisabazaar', 'policybazaar'],
  food: ['eatsure', 'magicpin', 'swiggy', 'zomato'],
  pharmacy: ['apollo247', 'netmeds', 'pharmeasy', 'tata1mg']
};

export type SourceCertificationCapture = {
  capture_version: string;
  run_id: string;
  case_id: string;
  domain: string;
  provider: string;
  query: string;
  captured_at: string;
  execution_mode: ScraperExecutionMode;
  scraper_component: string;
  message_type: string;
  requested_location_profile?: string;
  observed_location_evidence?: string;
  location_verified?: boolean;
  payload: any;
};

// Aliased for backward compatibility with existing tests
export type ScraperCertificationCaptureV1 = SourceCertificationCapture;

const EXACT_SENSITIVE_KEYS = new Set([
  'authorization',
  'cookie',
  'set-cookie',
  'access_token',
  'refresh_token',
  'session_id',
  'account_id',
  'email',
  'phone',
  'address',
  'device_id',
  'payment_token',
  'card_number',
  'x-session-id',
  'x-device-id'
]);

export function validateScraperCertificationCaptureV1(obj: any): obj is SourceCertificationCapture {
  if (!obj || typeof obj !== 'object') return false;
  if (obj.capture_version !== 'truecost.scraper.capture.v1') return false;
  if (typeof obj.run_id !== 'string' || !obj.run_id) return false;
  if (typeof obj.case_id !== 'string' || !obj.case_id) return false;
  
  if (typeof obj.domain !== 'string' || !obj.domain) return false;
  const validProviders = CertificationProviderRegistry[obj.domain.toLowerCase()];
  if (!validProviders) return false;
  if (!validProviders.includes(obj.provider?.toLowerCase())) return false;
  
  if (typeof obj.query !== 'string' || !obj.query) return false;
  
  if (!Date.parse(obj.captured_at)) return false;
  
  const validModes = ['REAL_LIVE_SCRAPE', 'REAL_CAPTURE_REPLAY', 'SYNTHETIC_MUTATION', 'MOCK'];
  if (!validModes.includes(obj.execution_mode)) return false;
  if (typeof obj.scraper_component !== 'string' || !obj.scraper_component) return false;
  if (typeof obj.message_type !== 'string' || !obj.message_type) return false;
  if (typeof obj.payload !== 'object' || obj.payload === null) return false;
  
  return true;
}

export function sanitizeCapture(payload: any): any {
  if (!payload || typeof payload !== 'object') {
    return payload;
  }

  if (Array.isArray(payload)) {
    return payload.map(item => sanitizeCapture(item));
  }

  const sanitized: any = {};
  for (const [key, value] of Object.entries(payload)) {
    if (EXACT_SENSITIVE_KEYS.has(key.toLowerCase())) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitizeCapture(value);
    } else {
      sanitized[key] = value;
    }
  }

  return sanitized;
}
