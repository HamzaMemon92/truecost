from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db import get_db
from app.api.endpoints.auth import current_user
from app.models import User
import json

router = APIRouter()

class PreferencesPayload(BaseModel):
    optimization_objective: Optional[str] = None   # cheapest | balanced | fastest
    dietary_flags: Optional[List[str]] = None       # veg, vegan, gluten_free etc.
    favorite_providers: Optional[List[str]] = None
    preferred_payment_methods: Optional[List[str]] = None  # upi, credit_card etc.
    notification_price_drops: Optional[bool] = True
    notification_deals: Optional[bool] = True
    notification_travel: Optional[bool] = True
    notification_activity: Optional[bool] = True
    accessibility_reduce_motion: Optional[bool] = False
    accessibility_large_text: Optional[bool] = False
    theme: Optional[str] = "system"   # light | dark | system
    language: Optional[str] = "en"

class PreferencesResponse(BaseModel):
    optimization_objective: str
    dietary_flags: List[str]
    favorite_providers: List[str]
    preferred_payment_methods: List[str]
    notification_price_drops: bool
    notification_deals: bool
    notification_travel: bool
    notification_activity: bool
    accessibility_reduce_motion: bool
    accessibility_large_text: bool
    theme: str
    language: str

DEFAULT_PREFS = PreferencesResponse(
    optimization_objective="balanced",
    dietary_flags=[],
    favorite_providers=[],
    preferred_payment_methods=["upi"],
    notification_price_drops=True,
    notification_deals=True,
    notification_travel=True,
    notification_activity=True,
    accessibility_reduce_motion=False,
    accessibility_large_text=False,
    theme="system",
    language="en",
)

def _parse_prefs(raw: Optional[str]) -> PreferencesResponse:
    if not raw:
        return DEFAULT_PREFS
    try:
        data = json.loads(raw)
        return PreferencesResponse(**{**DEFAULT_PREFS.dict(), **data})
    except Exception:
        return DEFAULT_PREFS

@router.get("", response_model=PreferencesResponse)
def get_preferences(
    current_user_obj: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> PreferencesResponse:
    """Retrieve the authenticated user's preferences."""
    prefs_json = getattr(current_user_obj, 'preferences_json', None)
    return _parse_prefs(prefs_json)

@router.put("", response_model=PreferencesResponse)
def update_preferences(
    payload: PreferencesPayload,
    current_user_obj: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> PreferencesResponse:
    """Update the authenticated user's preferences."""
    existing = _parse_prefs(getattr(current_user_obj, 'preferences_json', None))
    updated = existing.dict()
    for field, value in payload.dict(exclude_none=True).items():
        updated[field] = value
    
    if hasattr(current_user_obj, 'preferences_json'):
        current_user_obj.preferences_json = json.dumps(updated)
        db.commit()
        db.refresh(current_user_obj)
    
    return PreferencesResponse(**updated)
