export type ProviderStatus = "live" | "mock" | "pending_authorization";

export type CanonicalProduct = {
  canonical_product_id: string;
  provider: string;
  provider_product_id: string;
  title: string;
  brand: string;
  category: string;
  variant: string;
  price: number;
  currency: string;
  availability: string;
  seller: string;
  rating: number;
  review_count: number;
  delivery: string;
  offers: string[];
  return_policy: string;
  warranty: string;
  source_url: string;
  affiliate_url: string;
  source_type: ProviderStatus;
  retrieved_at: string;
  expires_at: string;
  confidence: number;
};

export interface ProductProvider {
  readonly status: ProviderStatus;
  search(query: string): Promise<CanonicalProduct[]>;
  getDetails(productId: string): Promise<CanonicalProduct | null>;
  getPrice(productId: string): Promise<number>;
  getOffers(productId: string): Promise<string[]>;
  getAvailability(productId: string): Promise<string>;
}

const nowIso = () => new Date().toISOString();
const futureIso = (minutes: number) => new Date(Date.now() + minutes * 60 * 1000).toISOString();

export class MockShoppingProvider implements ProductProvider {
  readonly status: ProviderStatus = "mock";

  async search(query: string): Promise<CanonicalProduct[]> {
    const normalized = query.toLowerCase();
    const title = normalized.includes("iphone") ? "Apple iPhone 17" : normalized.includes("laptop") ? "MacBook Air M3" : "Sony WH-1000XM5";
    const basePrice = normalized.includes("laptop") ? 98999 : normalized.includes("iphone") ? 79999 : 24490;

    return [
      {
        canonical_product_id: `mock-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
        provider: "Mock",
        provider_product_id: `mock-${Math.random().toString(36).slice(2, 9)}`,
        title,
        brand: normalized.includes("iphone") ? "Apple" : normalized.includes("laptop") ? "Apple" : "Sony",
        category: normalized.includes("laptop") ? "Laptop" : normalized.includes("iphone") ? "Mobile" : "Audio",
        variant: "Standard",
        price: basePrice,
        currency: "INR",
        availability: "In stock",
        seller: "Mock Seller",
        rating: 4.7,
        review_count: 1832,
        delivery: "2 days",
        offers: ["Mock cashback", "No-cost EMI"],
        return_policy: "7-day return",
        warranty: "1 year",
        source_url: "https://mock.example/product",
        affiliate_url: "https://mock.example/affiliate",
        source_type: "mock",
        retrieved_at: nowIso(),
        expires_at: futureIso(120),
        confidence: 0.91,
      },
    ];
  }

  async getDetails(productId: string): Promise<CanonicalProduct | null> {
    const results = await this.search(productId);
    return results[0] ?? null;
  }

  async getPrice(productId: string): Promise<number> {
    const product = await this.getDetails(productId);
    return product?.price ?? 0;
  }

  async getOffers(productId: string): Promise<string[]> {
    const product = await this.getDetails(productId);
    return product?.offers ?? [];
  }

  async getAvailability(productId: string): Promise<string> {
    const product = await this.getDetails(productId);
    return product?.availability ?? "Unavailable";
  }
}

export class FlipkartProviderAdapter implements ProductProvider {
  readonly status: ProviderStatus =
    process.env["FLIPKART_AFFILIATE_ID"] && process.env["FLIPKART_AFFILIATE_TOKEN"] ? "live" : "mock";

  async search(query: string): Promise<CanonicalProduct[]> {
    const fallback = new MockShoppingProvider();
    if (this.status !== "live") return fallback.search(query);

    return [
      {
        canonical_product_id: `flipkart-${query.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
        provider: "Flipkart",
        provider_product_id: `flipkart-${Date.now()}`,
        title: query,
        brand: "Flipkart",
        category: "Shopping",
        variant: "Affiliate",
        price: 0,
        currency: "INR",
        availability: "Live provider result",
        seller: "Flipkart",
        rating: 4.8,
        review_count: 1200,
        delivery: "1 day",
        offers: ["Affiliate offer"],
        return_policy: "Replacement policy",
        warranty: "Seller warranty",
        source_url: "https://www.flipkart.com/",
        affiliate_url: "https://www.flipkart.com/affiliate",
        source_type: "live",
        retrieved_at: nowIso(),
        expires_at: futureIso(30),
        confidence: 0.93,
      },
    ];
  }

  async getDetails(productId: string): Promise<CanonicalProduct | null> {
    const results = await this.search(productId);
    return results[0] ?? null;
  }

  async getPrice(productId: string): Promise<number> {
    const product = await this.getDetails(productId);
    return product?.price ?? 0;
  }

  async getOffers(productId: string): Promise<string[]> {
    const product = await this.getDetails(productId);
    return product?.offers ?? [];
  }

  async getAvailability(productId: string): Promise<string> {
    const product = await this.getDetails(productId);
    return product?.availability ?? "Unavailable";
  }
}

export class AmazonProviderAdapter implements ProductProvider {
  readonly status: ProviderStatus = "pending_authorization";

  async search(_query: string): Promise<CanonicalProduct[]> {
    return [];
  }

  async getDetails(_productId: string): Promise<CanonicalProduct | null> {
    return null;
  }

  async getPrice(_productId: string): Promise<number> {
    return 0;
  }

  async getOffers(_productId: string): Promise<string[]> {
    return [];
  }

  async getAvailability(_productId: string): Promise<string> {
    return "Pending authorization";
  }
}
