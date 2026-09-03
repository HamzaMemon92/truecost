from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Literal, Optional
from datetime import datetime, timezone
import hashlib
import random
import uuid
from app.graph.transit_workflow import compile_transit_workflow
transit_workflow = compile_transit_workflow()

from app.config import settings

router = APIRouter()

# --- Schemas ---

class FlightSearchRequest(BaseModel):
    origin: str = Field(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    destination: str = Field(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    departure_date: str  # ISO date string
    return_date: Optional[str] = None
    passengers: int = Field(default=1, ge=1, le=9)
    cabin_class: Literal["economy", "business", "first"] = "economy"
    trip_type: Literal["one_way", "round_trip"] = "one_way"
    flexible_dates: bool = False

    @field_validator("origin", "destination")
    @classmethod
    def normalize_airport(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_itinerary(self):
        departure = _iso_date(self.departure_date, "departure_date")
        if self.origin == self.destination:
            raise ValueError("Origin and destination must be different")
        if self.trip_type == "round_trip":
            if not self.return_date:
                raise ValueError("return_date is required for a round trip")
            if _iso_date(self.return_date, "return_date") < departure:
                raise ValueError("return_date cannot be before departure_date")
        return self

class FlightOption(BaseModel):
    provider: str
    flight_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration_minutes: int
    stops: int
    cabin_class: str
    base_fare: float
    taxes_fees: float
    total_fare: float
    per_passenger_fare: float
    baggage_included: str
    cancellation_policy: str
    deep_link: str
    data_source: str
    authoritative: bool = False
    freshness_state: Literal["verified", "preview", "stale", "unavailable"] = "preview"
    source_freshness: str = "development_preview"

class FlightSearchResult(BaseModel):
    search_id: str
    origin: str
    destination: str
    departure_date: str
    passengers: int
    cabin_class: str
    options: List[FlightOption]
    cheapest_option: Optional[FlightOption]
    recommendation_reason: str
    generated_at: str
    disclaimer: str

class HotelSearchRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=120)
    checkin_date: str
    checkout_date: str
    guests: int = Field(default=2, ge=1, le=30)
    rooms: int = Field(default=1, ge=1, le=10)
    budget_max: Optional[float] = Field(default=None, gt=0)
    star_rating_min: Optional[int] = Field(default=None, ge=1, le=5)

    @model_validator(mode="after")
    def validate_stay(self):
        checkin = _iso_date(self.checkin_date, "checkin_date")
        checkout = _iso_date(self.checkout_date, "checkout_date")
        if checkout <= checkin:
            raise ValueError("checkout_date must be after checkin_date")
        return self

class HotelOption(BaseModel):
    provider: str
    hotel_name: str
    star_rating: int
    location: str
    price_per_night: float
    total_price: float
    taxes_fees: float
    cancellation_policy: str
    breakfast_included: bool
    amenities: List[str]
    deep_link: str
    data_source: str
    authoritative: bool = False
    freshness_state: Literal["verified", "preview", "stale", "unavailable"] = "preview"
    source_freshness: str = "development_preview"

class HotelSearchResult(BaseModel):
    search_id: str
    destination: str
    checkin_date: str
    checkout_date: str
    nights: int
    guests: int
    options: List[HotelOption]
    best_value_option: Optional[HotelOption]
    recommendation_reason: str
    generated_at: str
    disclaimer: str

# --- Popular Routes for UI ---
POPULAR_ROUTES = [
    {"origin": "DEL", "origin_city": "Delhi", "destination": "BOM", "destination_city": "Mumbai"},
    {"origin": "BOM", "origin_city": "Mumbai", "destination": "BLR", "destination_city": "Bengaluru"},
    {"origin": "DEL", "origin_city": "Delhi", "destination": "BLR", "destination_city": "Bengaluru"},
    {"origin": "BLR", "origin_city": "Bengaluru", "destination": "HYD", "destination_city": "Hyderabad"},
    {"origin": "DEL", "origin_city": "Delhi", "destination": "GOI", "destination_city": "Goa"},
    {"origin": "BOM", "origin_city": "Mumbai", "destination": "GOI", "destination_city": "Goa"},
]

AIRPORTS = {
    "DEL": "Indira Gandhi International Airport, New Delhi",
    "BOM": "Chhatrapati Shivaji Maharaj International Airport, Mumbai",
    "BLR": "Kempegowda International Airport, Bengaluru",
    "HYD": "Rajiv Gandhi International Airport, Hyderabad",
    "GOI": "Goa International Airport, Goa",
    "MAA": "Chennai International Airport, Chennai",
    "CCU": "Netaji Subhas Chandra Bose International Airport, Kolkata",
    "PNQ": "Pune Airport, Pune",
    "AMD": "Sardar Vallabhbhai Patel International Airport, Ahmedabad",
    "COK": "Cochin International Airport, Kochi",
}

def _iso_date(value: str, field_name: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD") from exc

def _stable_random(*values: str) -> random.Random:
    digest = hashlib.sha256("|".join(values).encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))

# --- Routes ---

@router.post("/flights/search", response_model=FlightSearchResult)
async def search_flights(req: FlightSearchRequest) -> FlightSearchResult:
    """
    Search flights across providers.
    Returns mock structured data as live provider APIs require credentials.
    UI must display data_source to users.
    """
    if not settings.provider_preview_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Verified flight inventory is not available")
    providers = [
        {"name": "MakeMyTrip", "link": f"https://www.makemytrip.com/flight/search?tripType=O&itinerary={req.origin}-{req.destination}-{req.departure_date}&paxType=A-{req.passengers}_C-0_I-0&cabinClass={req.cabin_class.upper()}"},
        {"name": "Goibibo",    "link": f"https://www.goibibo.com/flights/search/{req.origin}-{req.destination}-{req.departure_date}-{req.passengers}-0-0-E"},
        {"name": "Ixigo",      "link": f"https://www.ixigo.com/search/result/flight/{req.origin}/{req.destination}/{req.departure_date}/{req.passengers}/0/0/E/CHEAPEST"},
        {"name": "Cleartrip", "link": f"https://www.cleartrip.com/flights/results?from={req.origin}&to={req.destination}&depart_date={req.departure_date}&adults={req.passengers}&class={req.cabin_class}"},
    ]

    # Realistic mock fares per route for demo/dev purposes
    base_fares = {"economy": 4500, "business": 18000, "first": 40000}
    trip_multiplier = 2 if req.trip_type == "round_trip" else 1
    base = base_fares.get(req.cabin_class, 4500) * req.passengers * trip_multiplier
    duration_map = {("DEL","BOM"): 130, ("BOM","BLR"): 90, ("DEL","BLR"): 155, ("BLR","HYD"): 55, ("DEL","GOI"): 130, ("BOM","GOI"): 55}
    duration = duration_map.get((req.origin, req.destination), 120)

    rng = _stable_random(req.origin, req.destination, req.departure_date, req.return_date or "", req.cabin_class, str(req.passengers))

    options = []
    for i, prov in enumerate(providers):
        variance = rng.uniform(0.85, 1.20)
        fare = round(base * variance)
        taxes = round(fare * 0.18)
        total = fare + taxes
        dep_hour = 6 + (i * 3)
        arr_min = dep_hour * 60 + duration
        arr_hour = arr_min // 60
        arr_minute = arr_min % 60
        options.append(FlightOption(
            provider=prov["name"],
            flight_number=f"TC{rng.randint(100,999)}",
            origin=req.origin,
            destination=req.destination,
            departure_time=f"{dep_hour:02d}:00",
            arrival_time=f"{arr_hour:02d}:{arr_minute:02d}",
            duration_minutes=duration,
            stops=0 if duration < 120 else 1,
            cabin_class=req.cabin_class,
            base_fare=float(fare),
            taxes_fees=float(taxes),
            total_fare=float(total),
            per_passenger_fare=round(float(total)/req.passengers, 2),
            baggage_included="15kg check-in + 7kg cabin" if req.cabin_class == "economy" else "30kg check-in + 7kg cabin",
            cancellation_policy="Free cancellation up to 24h before departure" if i % 2 == 0 else "Non-refundable",
            deep_link=prov["link"],
            data_source="mock_dev_data",
        ))

    cheapest = min(options, key=lambda x: x.total_fare)
    return FlightSearchResult(
        search_id=str(uuid.uuid4()),
        origin=req.origin,
        destination=req.destination,
        departure_date=req.departure_date,
        passengers=req.passengers,
        cabin_class=req.cabin_class,
        options=options,
        cheapest_option=cheapest,
        recommendation_reason=f"{cheapest.provider} has the lowest total fare of Rs.{cheapest.total_fare:.0f} for {req.passengers} passenger(s).",
        generated_at=datetime.now(timezone.utc).isoformat(),
        disclaimer="Development preview data, not live inventory. Final price and availability must be confirmed with the provider.",
    )


@router.get("/flights/popular-routes")
async def popular_routes():
    return {"routes": POPULAR_ROUTES}


@router.get("/flights/airports")
async def search_airports(q: str = Query("", min_length=1)):
    results = [
        {"code": code, "name": name}
        for code, name in AIRPORTS.items()
        if q.upper() in code or q.lower() in name.lower()
    ]
    return {"airports": results}


@router.post("/hotels/search", response_model=HotelSearchResult)
async def search_hotels(req: HotelSearchRequest) -> HotelSearchResult:
    """Search hotels across providers with mock pricing."""
    if not settings.provider_preview_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Verified hotel inventory is not available")
    ci = _iso_date(req.checkin_date, "checkin_date")
    co = _iso_date(req.checkout_date, "checkout_date")
    nights = (co - ci).days

    providers = [
        {"name": "MakeMyTrip", "link": f"https://www.makemytrip.com/hotels"},
        {"name": "Goibibo",    "link": f"https://www.goibibo.com/hotels"},
        {"name": "Booking.com","link": f"https://www.booking.com/searchresults.html?ss={req.destination}"},
        {"name": "Agoda",      "link": f"https://www.agoda.com/search?city={req.destination}"},
    ]

    rng = _stable_random(req.destination, req.checkin_date, req.checkout_date, str(req.rooms), str(req.guests))

    options = []
    hotel_names = ["Grand Residency", "City Comfort Inn", "The Urban Nest", "Skyline Suites"]
    for i, prov in enumerate(providers):
        stars = rng.randint(3, 5)
        if req.star_rating_min and stars < req.star_rating_min:
            continue
        base_price = {3: 2500, 4: 5000, 5: 12000}.get(stars, 3500)
        price_per_night = round(base_price * rng.uniform(0.85, 1.25) * req.rooms)
        if req.budget_max and price_per_night > req.budget_max:
            continue
        total = round(price_per_night * nights)
        taxes = round(total * 0.12)
        options.append(HotelOption(
            provider=prov["name"],
            hotel_name=f"{hotel_names[i % len(hotel_names)]} {req.destination}",
            star_rating=stars,
            location=req.destination,
            price_per_night=float(price_per_night),
            total_price=float(total + taxes),
            taxes_fees=float(taxes),
            cancellation_policy="Free cancellation until 24h before check-in" if i % 2 == 0 else "Non-refundable",
            breakfast_included=stars >= 4,
            amenities=["Free WiFi", "AC"] + (["Pool", "Gym"] if stars >= 4 else []) + (["Spa"] if stars == 5 else []),
            deep_link=prov["link"],
            data_source="mock_dev_data",
        ))

    best = min(options, key=lambda x: x.total_price) if options else None
    return HotelSearchResult(
        search_id=str(uuid.uuid4()),
        destination=req.destination,
        checkin_date=req.checkin_date,
        checkout_date=req.checkout_date,
        nights=nights,
        guests=req.guests,
        options=options,
        best_value_option=best,
        recommendation_reason=f"{best.provider} has the lowest generated preview total of Rs.{best.total_price:.0f} for {nights} night(s)." if best else "No development preview option matched these filters.",
        generated_at=datetime.now(timezone.utc).isoformat(),
        disclaimer="Development preview data, not live inventory. Final price and availability must be confirmed with the provider.",
    )
