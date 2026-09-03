from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.endpoints.auth import bearer, current_user
from app.db import get_db
from app.models import SupportReport, User
from app.security import decode_token

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(current_user)]
ReportCategory = Literal["wrong_price", "wrong_product", "broken_link", "refund_help", "other"]


class ReportInput(BaseModel):
    category: ReportCategory
    subject: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=4000)
    provider: str | None = Field(default=None, max_length=100)
    source_url: str | None = Field(default=None, max_length=2000)
    product_id: str | None = Field(default=None, max_length=300)


class ReportResponse(ReportInput):
    id: str
    status: str
    created_at: datetime


def _response(row: SupportReport) -> ReportResponse:
    return ReportResponse(id=row.id, category=row.category, subject=row.subject, description=row.description, provider=row.provider, source_url=row.source_url, product_id=row.product_id, status=row.status, created_at=row.created_at)


def _optional_user(credentials: HTTPAuthorizationCredentials | None, db: Session) -> User | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    claims = decode_token(credentials.credentials, "access")
    return db.get(User, claims["sub"])


@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(payload: ReportInput, db: Db, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> ReportResponse:
    user = _optional_user(credentials, db)
    row = SupportReport(user_id=user.id if user else None, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _response(row)


@router.get("/reports", response_model=list[ReportResponse])
def list_my_reports(db: Db, user: CurrentUser) -> list[ReportResponse]:
    rows = db.scalars(select(SupportReport).where(SupportReport.user_id == user.id).order_by(SupportReport.created_at.desc())).all()
    return [_response(row) for row in rows]


@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_my_report(report_id: str, db: Db, user: CurrentUser) -> ReportResponse:
    row = db.scalar(select(SupportReport).where(SupportReport.id == report_id, SupportReport.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return _response(row)
