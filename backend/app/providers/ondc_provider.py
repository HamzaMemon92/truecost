import os
from typing import Any
import asyncio
from datetime import datetime, timezone

from app.schemas.grocery import Location, CanonicalGroceryItem
from app.providers.grocery_base import GroceryProvider

class OndcNetworkProvider(GroceryProvider):
    """
    ONDC Buyer Network Participant (BNP) Adapter for RET10 (Grocery).
    This acts as a network-level boundary, not a retailer-level boundary.
    It expects a single search to yield multiple offers from distinct sellers.
    """

    def __init__(self, timeout_ms: int = 4500):
        self.name = "ONDC_Network"
        self.status = "active"
        
        # Determine environment constraints
        raw_env = os.environ.get("ONDC_ENV", "mock").lower()
        if raw_env in ("staging", "preprod", "live"):
            self.source_type = raw_env
        else:
            self.source_type = "mock"
            
        self.timeout_ms = timeout_ms

    async def search(self, query: str, location: Location | None = None) -> list[CanonicalGroceryItem] | list[dict[str, Any]]:
        """
        Executes a true ONDC network search (Beckn Protocol).
        
        Official ONDC Specification (RET10):
        The search payload must strictly include:
        - context: domain (ONDC:RET10), action (search), version (1.2.0 or current), 
                   bap_id, bap_uri, transaction_id, message_id, timestamp, ttl, city, country
        - message: intent (category, item name, or fulfillment location)
        
        Authentication:
        Must include an HTTP 'Authorization' header with a detached Ed25519 signature
        signed by the private key registered for the BAP in the ONDC registry.
        
        Asynchronous Lifecycle:
        - This synchronous `search` method sends the POST /search request to ONDC Gateway or BPPs.
        - Results arrive asynchronously to the `ONDC_BAP_URI` via POST /on_search webhooks.
        - TrueCost requires a messaging queue (e.g. Redis) or WebSocket signaling to yield results here.
        """
        
        if self.source_type not in ("staging", "preprod", "live"):
            raise ValueError(f"OndcNetworkProvider requires ONDC_ENV to be staging, preprod, or live. Got {self.source_type}")
            
        bap_id = os.environ.get("ONDC_BAP_ID")
        bap_uri = os.environ.get("ONDC_BAP_URI")
        private_key = os.environ.get("ONDC_PRIVATE_KEY")
        
        if not bap_id or not bap_uri or not private_key:
            raise ValueError("Live ONDC execution blocked: Missing ONDC_BAP_ID, ONDC_BAP_URI, or ONDC_PRIVATE_KEY configuration.")
            
        if self.source_type == "live":
            raise NotImplementedError("PRODUCTION ONDC execution is explicitly blocked pending official certification and verified real-world cryptography.")
        
        # Placeholder for actual network execution over Staging/Preprod
        raise NotImplementedError(f"ONDC {self.source_type.upper()} execution requires asynchronous webhook infrastructure (e.g., Celery/Redis).")

    def _normalize_ondc_item(self, bpp_id: str, provider_id: str, item: dict[str, Any]) -> dict[str, Any]:
        """
        Helper method to normalize a raw ONDC catalog item into the TrueCost domain object.
        Preserves the seller identity and GTIN for accurate canonical grouping.
        """
        now = datetime.now(timezone.utc)
        
        # Extract GTIN/EAN from ONDC standard item description descriptor
        gtin = None
        if "descriptor" in item and "code" in item["descriptor"]:
            # ONDC often uses 1:EAN or similar tagging
            code = item["descriptor"].get("code", "")
            if code.startswith("1:"):
                gtin = code.split(":")[1]

        seller_name = f"ONDC Seller {provider_id}"
        
        return {
            "canonical_product_id": gtin, # Falls back to adapter title normalization if None
            "provider": seller_name,
            "provider_sku": f"{bpp_id}:{provider_id}:{item.get('id', 'unknown')}",
            "title": item.get("descriptor", {}).get("name", "Unknown Product"),
            "price": float(item.get("price", {}).get("value", 0.0)),
            "mrp": float(item.get("price", {}).get("maximum_value", 0.0)) if "maximum_value" in item.get("price", {}) else None,
            "availability": "IN_STOCK" if int(item.get("quantity", {}).get("available", {}).get("count", 0)) > 0 else "OUT_OF_STOCK",
            "retrieved_at": now,
            "source_type": self.source_type,
            "image_confidence": "KNOWN_SOURCE", # ONDC imagery is never blindly TRUSTED
            "currency": item.get("price", {}).get("currency", "INR")
        }
