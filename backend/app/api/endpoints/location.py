from __future__ import annotations
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class ServiceabilityRequest(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    pincode: Optional[str] = None
    city: Optional[str] = None

class ProviderServiceability(BaseModel):
    provider: str
    category: str
    is_serviceable: bool
    estimated_delivery: Optional[str] = None
    reason: Optional[str] = None

class ServiceabilityResult(BaseModel):
    location_label: str
    pincode: Optional[str]
    city: Optional[str]
    is_any_serviceable: bool
    providers: List[ProviderServiceability]
    generated_at: str
    disclaimer: str

class SavedAddress(BaseModel):
    id: str
    label: str  # Home, Work, Other
    address_line: str
    city: str
    pincode: str
    lat: Optional[float] = None
    lng: Optional[float] = None

# Major Indian serviceable pincodes (sample — production would use real DB)
SERVICEABLE_CITIES = {
    "mumbai": ["400001","400002","400003","400050","400051","400052"],
    "delhi": ["110001","110002","110003","110004","110005","110006"],
    "bengaluru": ["560001","560002","560003","560004","560005"],
    "hyderabad": ["500001","500002","500003","500004"],
    "chennai": ["600001","600002","600003"],
}

GROCERY_PROVIDERS = ["Zepto", "Blinkit", "Swiggy Instamart", "BigBasket"]
MOBILITY_PROVIDERS = ["Uber", "Ola", "Rapido"]
SHOPPING_PROVIDERS = ["Amazon", "Flipkart"]
FOOD_PROVIDERS = ["Swiggy Food", "Zomato"]

def _detect_city(pincode: Optional[str], lat: Optional[float], lng: Optional[float]) -> Optional[str]:
    if pincode:
        for city, pins in SERVICEABLE_CITIES.items():
            if pincode in pins:
                return city
    if lat and lng:
        if 18.8 <= lat <= 19.3 and 72.7 <= lng <= 73.1: return "mumbai"
        if 28.4 <= lat <= 28.9 and 76.8 <= lng <= 77.4: return "delhi"
        if 12.8 <= lat <= 13.2 and 77.4 <= lng <= 77.8: return "bengaluru"
        if 17.2 <= lat <= 17.6 and 78.3 <= lng <= 78.7: return "hyderabad"
        if 12.9 <= lat <= 13.3 and 80.1 <= lng <= 80.4: return "chennai"
    return None

@router.post("/serviceability", response_model=ServiceabilityResult)
async def check_serviceability(req: ServiceabilityRequest) -> ServiceabilityResult:
    """Check which TrueCost provider categories are available at a given location."""
    city = _detect_city(req.pincode, req.lat, req.lng)
    is_metro = city is not None
    location_label = city.title() if city else (req.city or "Unknown Location")

    providers: List[ProviderServiceability] = []
    
    for p in GROCERY_PROVIDERS:
        providers.append(ProviderServiceability(
            provider=p, category="grocery", is_serviceable=is_metro,
            estimated_delivery="10-30 mins" if is_metro else None,
            reason=None if is_metro else "Currently not available in your area"
        ))

    for p in MOBILITY_PROVIDERS:
        providers.append(ProviderServiceability(
            provider=p, category="mobility", is_serviceable=is_metro,
            estimated_delivery=None, reason=None if is_metro else "Currently not available in your area"
        ))

    for p in SHOPPING_PROVIDERS:
        providers.append(ProviderServiceability(
            provider=p, category="shopping", is_serviceable=True,
            estimated_delivery="1-5 days", reason=None
        ))

    for p in FOOD_PROVIDERS:
        providers.append(ProviderServiceability(
            provider=p, category="food", is_serviceable=is_metro,
            estimated_delivery="30-45 mins" if is_metro else None,
            reason=None if is_metro else "Currently not available in your area"
        ))

    return ServiceabilityResult(
        location_label=location_label, pincode=req.pincode, city=city,
        is_any_serviceable=True, providers=providers,
        generated_at=datetime.utcnow().isoformat(),
        disclaimer="Serviceability is indicative. Actual availability confirmed at provider checkout."
    )

@router.get("/popular-cities")
async def popular_cities():
    return {
        "cities": [
            {"name": "Mumbai",    "pincode": "400001", "lat": 19.0760, "lng": 72.8777},
            {"name": "Delhi",     "pincode": "110001", "lat": 28.6139, "lng": 77.2090},
            {"name": "Bengaluru", "pincode": "560001", "lat": 12.9716, "lng": 77.5946},
            {"name": "Hyderabad", "pincode": "500001", "lat": 17.3850, "lng": 78.4867},
            {"name": "Chennai",   "pincode": "600001", "lat": 13.0827, "lng": 80.2707},
        ]
    }
