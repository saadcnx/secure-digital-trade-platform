import os
import secrets
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from privacy_governance.pii_protection import PIIProtectionService
from privacy_governance.region_store import (
    RegionalPrivacyStore,
    RegionRoutingError,
)


load_dotenv()

PRIVACY_API_KEY = os.getenv("PRIVACY_API_KEY")
if not PRIVACY_API_KEY:
    raise RuntimeError("PRIVACY_API_KEY is missing from .env")

pii_service = PIIProtectionService()
privacy_store = RegionalPrivacyStore(pii_service)

app = FastAPI(
    title="Privacy Governance Demo",
    version="1.0.0",
    description=(
        "Educational Presidio PII redaction, regional routing simulation, "
        "and erasure workflow. Not a GDPR certification."
    ),
)


def require_privacy_api_key(
    x_privacy_api_key: str | None = Header(default=None),
) -> None:
    if not x_privacy_api_key or not secrets.compare_digest(
        x_privacy_api_key,
        PRIVACY_API_KEY,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing privacy demo API key",
        )


class TextRedactionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class CustomerOrderRequest(BaseModel):
    user_id: str = Field(min_length=3, max_length=80)
    country_code: str = Field(min_length=2, max_length=2)
    customer_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    phone: str = Field(min_length=3, max_length=40)
    address: str = Field(min_length=3, max_length=300)
    notes: str = Field(default="", max_length=2000)
    amount_usd: float = Field(gt=0, le=1_000_000)


class ErasureRequest(BaseModel):
    user_id: str = Field(min_length=3, max_length=80)
    country_code: str = Field(min_length=2, max_length=2)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "privacy_governance_demo",
    }


@app.post("/api/v1/privacy/anonymize")
def anonymize_text(
    request: TextRedactionRequest,
    _: None = Depends(require_privacy_api_key),
) -> dict[str, Any]:
    return pii_service.redact_text(request.text)


@app.post("/api/v1/privacy/records")
def save_privacy_record(
    request: CustomerOrderRequest,
    _: None = Depends(require_privacy_api_key),
) -> dict[str, Any]:
    try:
        return privacy_store.save_customer_order(request.model_dump())
    except RegionRoutingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/privacy/erase")
def erase_privacy_record(
    request: ErasureRequest,
    _: None = Depends(require_privacy_api_key),
) -> dict[str, Any]:
    try:
        return privacy_store.erase_customer(
            user_id=request.user_id,
            country_code=request.country_code,
        )
    except RegionRoutingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
