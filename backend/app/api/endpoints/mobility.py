from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime, timezone
import math
import uuid

from app.graph.transit_workflow import compile_transit_workflow
transit_workflow = compile_transit_workflow()


router = APIRouter()

# --- Schemas ---

class RideRequest(BaseModel):
    pickup_lat: float = Field(ge=-90, le=90)
    pickup_lng: float = Field(ge=-180, le=180)
    drop_lat: float = Field(ge=-90, le=90)
    drop_lng: float = Field(ge=-180, le=180)
    ride_class: Literal["standard", "premium", "auto", "bike"] = "standard"
    objective: Literal["cheapest", "fastest", "balanced", "comfort"] = "cheapest"

class ProviderFare(BaseModel):
    provider: str
    ride_class: str
    base_fare: float
    distance_fare: float
    time_fare: float
    surge_multiplier: float
    platform_fee: float
    total_fare: float
    eta_minutes: int
    is_available: bool
    deep_link: str
    is_surge: bool
    promo_available: bool
    promo_code: Optional[str] = None
    promo_savings: float = 0.0

class MobilityComparisonResult(BaseModel):
    request_id: str
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float
    estimated_distance_km: float
    estimated_duration_minutes: int
    provider_fares: List[ProviderFare]
    recommended_provider: str
    recommendation_reason: str
    truecost_winner: ProviderFare
    objective: str
    generated_at: str
    data_source: str  # always "estimated" - never present as live fare

# --- Helpers ---

def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate straight-line distance between two GPS points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def estimate_road_distance(straight_km: float) -> float:
    """Road distance is typically 1.3x straight-line in Indian cities."""
    return round(straight_km * 1.35, 2)

def estimate_duration(road_km: float) -> int:
    """Estimate duration assuming 20km/h average in Indian traffic."""
    return max(5, int((road_km / 20) * 60))

def calculate_fare(
    provider: str,
    ride_class: str,
    distance_km: float,
    duration_min: int,
    pickup_lat: float,
    pickup_lng: float,
    drop_lat: float,
    drop_lng: float,
    surge: float = 1.0,
) -> ProviderFare:
    """Calculate estimated fare using publicly known fare structures."""

    # Publicly known base fare structures (INR)
    FARE_CONFIG = {
        "Uber": {
            "standard": {"base": 30, "per_km": 12, "per_min": 1.5, "platform_fee": 5},
            "premium":  {"base": 50, "per_km": 18, "per_min": 2.0, "platform_fee": 8},
            "auto":     {"base": 20, "per_km": 9,  "per_min": 1.0, "platform_fee": 3},
            "bike":     {"base": 15, "per_km": 5,  "per_min": 0.5, "platform_fee": 2},
        },
        "Ola": {
            "standard": {"base": 28, "per_km": 11, "per_min": 1.2, "platform_fee": 4},
            "premium":  {"base": 45, "per_km": 16, "per_min": 1.8, "platform_fee": 7},
            "auto":     {"base": 18, "per_km": 8,  "per_min": 0.9, "platform_fee": 2},
            "bike":     {"base": 12, "per_km": 4.5,"per_min": 0.4, "platform_fee": 2},
        },
        "Rapido": {
            "standard": {"base": 25, "per_km": 10, "per_min": 1.0, "platform_fee": 3},
            "premium":  {"base": 40, "per_km": 15, "per_min": 1.6, "platform_fee": 6},
            "auto":     {"base": 15, "per_km": 7,  "per_min": 0.8, "platform_fee": 2},
            "bike":     {"base": 10, "per_km": 4,  "per_min": 0.35,"platform_fee": 1},
        },
    }

    config = FARE_CONFIG.get(provider, FARE_CONFIG["Uber"]).get(ride_class, FARE_CONFIG["Uber"]["standard"])

    base_fare = config["base"]
    distance_fare = round(config["per_km"] * distance_km, 2)
    time_fare = round(config["per_min"] * duration_min, 2)
    platform_fee = config["platform_fee"]
    subtotal = base_fare + distance_fare + time_fare
    total = round((subtotal * surge) + platform_fee, 2)

    # ETA varies by provider
    eta_map = {"Uber": 5, "Ola": 6, "Rapido": 4}
    eta = eta_map.get(provider, 6) + int(distance_km * 0.5)

    deep_links = {
        "Uber": f"uber://?action=setPickup&pickup[latitude]={pickup_lat}&pickup[longitude]={pickup_lng}&dropoff[latitude]={drop_lat}&dropoff[longitude]={drop_lng}",
        "Ola": "olacabs://",
        "Rapido": "in.rapido.passenger://",
    }

    return ProviderFare(
        provider=provider,
        ride_class=ride_class,
        base_fare=base_fare,
        distance_fare=distance_fare,
        time_fare=time_fare,
        surge_multiplier=surge,
        platform_fee=platform_fee,
        total_fare=total,
        eta_minutes=eta,
        is_available=True,
        deep_link=deep_links.get(provider, ""),
        is_surge=surge > 1.0,
        promo_available=False,
        promo_savings=0.0,
    )

# --- Routes ---

@router.post("/compare", response_model=MobilityComparisonResult)
async def compare_mobility(
    req: RideRequest,
) -> MobilityComparisonResult:
    """
    Compare Uber, Ola, and Rapido fares for a given route.
    Returns estimated fares based on publicly known fare structures.
    Actual fares confirmed at provider checkout.
    """
    straight_km = haversine_km(req.pickup_lat, req.pickup_lng, req.drop_lat, req.drop_lng)
    if straight_km < 0.1:
        raise HTTPException(status_code=400, detail="Pickup and drop locations are too close.")

    road_km = estimate_road_distance(straight_km)
    duration_min = estimate_duration(road_km)

    providers = ["Uber", "Ola", "Rapido"]
    fares = [calculate_fare(p, req.ride_class, road_km, duration_min, req.pickup_lat, req.pickup_lng, req.drop_lat, req.drop_lng) for p in providers]

    # Select winner based on objective
    if req.objective == "cheapest":
        winner = min(fares, key=lambda f: f.total_fare)
        reason = f"{winner.provider} has the lowest estimated fare of ₹{winner.total_fare:.0f} for this route."
    elif req.objective == "fastest":
        winner = min(fares, key=lambda f: f.eta_minutes)
        reason = f"{winner.provider} has the fastest estimated pickup of {winner.eta_minutes} minutes."
    elif req.objective == "comfort":
        winner = min(fares, key=lambda f: (f.surge_multiplier, f.eta_minutes, f.total_fare))
        reason = f"{winner.provider} is the comfort pick because it has the lowest surge exposure with a {winner.eta_minutes} minute pickup estimate."
    else:  # balanced
        # Score: lower is better, normalize cost and time
        max_fare = max(f.total_fare for f in fares)
        max_eta = max(f.eta_minutes for f in fares)
        def balance_score(f):
            cost_score = f.total_fare / max_fare if max_fare > 0 else 0
            time_score = f.eta_minutes / max_eta if max_eta > 0 else 0
            return (cost_score * 0.6) + (time_score * 0.4)
        winner = min(fares, key=balance_score)
        reason = f"{winner.provider} offers the best balance of cost (₹{winner.total_fare:.0f}) and speed ({winner.eta_minutes} min)."

    return MobilityComparisonResult(
        request_id=str(uuid.uuid4()),
        pickup_lat=req.pickup_lat,
        pickup_lng=req.pickup_lng,
        drop_lat=req.drop_lat,
        drop_lng=req.drop_lng,
        estimated_distance_km=road_km,
        estimated_duration_minutes=duration_min,
        provider_fares=fares,
        recommended_provider=winner.provider,
        recommendation_reason=reason,
        truecost_winner=winner,
        objective=req.objective,
        generated_at=datetime.now(timezone.utc).isoformat(),
        data_source="estimated_reference_formula",
    )


@router.get("/providers")
async def list_mobility_providers():
    """Return metadata about supported mobility providers."""
    return {
        "providers": [
            {"id": "uber", "name": "Uber", "classes": ["standard", "premium", "auto"], "logo": "uber"},
            {"id": "ola",  "name": "Ola",  "classes": ["standard", "premium", "auto", "bike"], "logo": "ola"},
            {"id": "rapido", "name": "Rapido", "classes": ["standard", "auto", "bike"], "logo": "rapido"},
        ],
        "disclaimer": "Fares are estimates based on publicly known pricing. Actual fares are confirmed at provider checkout."
    }
