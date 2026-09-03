export type ImageConfidence = "TRUSTED" | "KNOWN_SOURCE" | "FALLBACK" | "UNVERIFIED";

export interface ResolvedImage {
  url: string | null;
  source: string | null;
  confidence: ImageConfidence;
  isFallback: boolean;
}

export function resolveProductImage(product: any, offer?: any): ResolvedImage {
  // 1. Verified retailer SKU image takes absolute precedence for that specific offer
  if (offer && offer.image_verified && offer.retailer_image_url) {
    return {
      url: offer.retailer_image_url,
      source: offer.image_source || "retailer",
      confidence: "TRUSTED",
      isFallback: false
    };
  }

  // 2. Verified canonical variant image
  if (product && product.image_url && product.image_confidence === "TRUSTED") {
    return {
      url: product.image_url,
      source: product.image_source || "canonical",
      confidence: "TRUSTED",
      isFallback: false
    };
  }

  // 3. Known source but unverified (e.g., matching text but not exact variant)
  if (product && product.image_url && product.image_confidence === "KNOWN_SOURCE") {
    return {
      url: product.image_url,
      source: product.image_source || "canonical",
      confidence: "KNOWN_SOURCE",
      isFallback: false
    };
  }

  // 4. Fallback or neutral placeholder
  return {
    url: null, // Signals the UI to use a neutral category icon
    source: "system",
    confidence: "FALLBACK",
    isFallback: true
  };
}
