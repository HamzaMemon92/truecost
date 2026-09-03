import { sanitizeCapture, validateScraperCertificationCaptureV1, SourceCertificationCapture } from '../sanitizeCapture';

describe('validateScraperCertificationCaptureV1', () => {
  it('validates a correct envelope', () => {
    const valid: SourceCertificationCapture = {
      capture_version: 'truecost.scraper.capture.v1',
      run_id: 'run123',
      case_id: 'test_case',
      provider: 'blinkit',
      domain: 'grocery',
      query: 'milk',
      captured_at: new Date().toISOString(),
      execution_mode: 'REAL_LIVE_SCRAPE',
      scraper_component: 'BlinkitScraper',
      message_type: 'SEARCH_SUCCESS',
      requested_location_profile: 'delhi',
      observed_location_evidence: 'lat:28,lng:77',
      location_verified: true,
      payload: { data: 'test' }
    };
    expect(validateScraperCertificationCaptureV1(valid)).toBe(true);
  });

  it('rejects invalid provider', () => {
    const invalid = {
      capture_version: 'truecost.scraper.capture.v1', run_id: 'run123',
      case_id: '123', provider: 'invalid_provider', domain: 'grocery', query: 'milk',
      captured_at: new Date().toISOString(), execution_mode: 'REAL_LIVE_SCRAPE', scraper_component: 'S', message_type: 'S',
      requested_location_profile: 'delhi', observed_location_evidence: 'lat', location_verified: true, payload: {}
    };
    expect(validateScraperCertificationCaptureV1(invalid)).toBe(false);
  });

  it('rejects missing or empty query', () => {
    const invalid = {
      capture_version: 'truecost.scraper.capture.v1', run_id: 'run123',
      case_id: '123', provider: 'blinkit', domain: 'grocery', query: '',
      captured_at: new Date().toISOString(), execution_mode: 'REAL_LIVE_SCRAPE', scraper_component: 'S', message_type: 'S',
      requested_location_profile: 'delhi', observed_location_evidence: 'lat', location_verified: true, payload: {}
    };
    expect(validateScraperCertificationCaptureV1(invalid)).toBe(false);
  });

  it('rejects invalid execution mode', () => {
    const invalid = {
      capture_version: 'truecost.scraper.capture.v1', run_id: 'run123',
      case_id: '123', provider: 'blinkit', domain: 'grocery', query: 'milk',
      captured_at: new Date().toISOString(), execution_mode: 'FAKE_MODE', scraper_component: 'S', message_type: 'S',
      requested_location_profile: 'delhi', observed_location_evidence: 'lat', location_verified: true, payload: {}
    };
    expect(validateScraperCertificationCaptureV1(invalid)).toBe(false);
  });
});

describe('sanitizeCapture', () => {
  it('redacts Authorization', () => {
    expect(sanitizeCapture({ Authorization: 'Bearer 123' }).Authorization).toBe('[REDACTED]');
    expect(sanitizeCapture({ authorization: 'Bearer 123' }).authorization).toBe('[REDACTED]');
  });

  it('redacts Cookie and Set-Cookie exactly', () => {
    expect(sanitizeCapture({ Cookie: 'session=1' }).Cookie).toBe('[REDACTED]');
    expect(sanitizeCapture({ 'Set-Cookie': 'session=1' })['Set-Cookie']).toBe('[REDACTED]');
  });

  it('redacts tokens EXACTLY', () => {
    expect(sanitizeCapture({ access_token: '123' }).access_token).toBe('[REDACTED]');
    expect(sanitizeCapture({ refresh_token: '123' }).refresh_token).toBe('[REDACTED]');
  });

  it('redacts exact nested session and account data', () => {
    const input = { data: { session_id: '123', account_id: '456' } };
    const output = sanitizeCapture(input);
    expect(output.data.session_id).toBe('[REDACTED]');
    expect(output.data.account_id).toBe('[REDACTED]');
  });

  it('redacts exact nested arrays of sensitive objects', () => {
    const input = { items: [{ email: 'test@test.com' }, { phone: '1234567890' }] };
    const output = sanitizeCapture(input);
    expect(output.items[0].email).toBe('[REDACTED]');
    expect(output.items[1].phone).toBe('[REDACTED]');
  });

  it('redacts address and device_id exactly', () => {
    expect(sanitizeCapture({ address: '123 Main St' }).address).toBe('[REDACTED]');
    expect(sanitizeCapture({ device_id: 'device123' }).device_id).toBe('[REDACTED]');
  });

  it('redacts payment/card-like keys EXACTLY', () => {
    expect(sanitizeCapture({ payment_token: 'token123' }).payment_token).toBe('[REDACTED]');
    expect(sanitizeCapture({ card_number: '1234' }).card_number).toBe('[REDACTED]');
  });

  it('preserves provider commercial schema (product_cards, payment_offers)', () => {
    const input = {
      product_cards: [{ title: 'Amul Milk', price: 30 }],
      cards: [{ type: 'discount' }],
      payment_offers: [{ id: 1 }]
    };
    const output = sanitizeCapture(input);
    expect(output.product_cards[0].title).toBe('Amul Milk');
    expect(output.cards[0].type).toBe('discount');
    expect(output.payment_offers[0].id).toBe(1);
  });

  it('does not mutate original input and preserves safe fields', () => {
    const input = { name: 'Amul Milk', price: 20, access_token: '123' };
    const output = sanitizeCapture(input);
    expect(output.name).toBe('Amul Milk');
    expect(output.price).toBe(20);
    expect(output.access_token).toBe('[REDACTED]');
    expect(input.access_token).toBe('123');
  });
});
