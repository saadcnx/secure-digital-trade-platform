import os
import re
import secrets
from decimal import Decimal
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from compliance_engine.service import TradeComplianceService
from fraud_engine.service import FraudDetectionService
from payment_vault.currency import convert_currency
from payment_vault.tokenizer import PaymentTokenizer, TokenizationError
from privacy_governance.pii_protection import PIIProtectionService
from privacy_governance.region_store import (
    RegionalPrivacyStore,
    RegionRoutingError,
)


load_dotenv()

DEMO_API_KEY = os.getenv("DEMO_API_KEY")
FABRIC_BRIDGE_URL = os.getenv("FABRIC_BRIDGE_URL", "").rstrip("/")
DASHBOARD_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "dashboard",
    "index.html",
)

if not DEMO_API_KEY:
    raise RuntimeError("DEMO_API_KEY is missing from .env")

# These services load the local model/configuration at application startup.
fraud_service = FraudDetectionService()
compliance_service = TradeComplianceService()
payment_tokenizer = PaymentTokenizer()
pii_service = PIIProtectionService()
privacy_store = RegionalPrivacyStore(pii_service)

app = FastAPI(
    title="Global Trade Checkout Orchestrator",
    version="1.0.0",
    description=(
        "Educational local integration of fraud scoring, trade compliance, "
        "test-card tokenization, and privacy-routing modules."
    ),
)


def require_demo_api_key(
    x_demo_api_key: str | None = Header(default=None),
) -> None:
    if not x_demo_api_key or not secrets.compare_digest(
        x_demo_api_key,
        DEMO_API_KEY,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing demo API key",
        )


class TelemetryInput(BaseModel):
    checkout_duration_sec: float = Field(default=20, ge=0, le=3600)
    mouse_movement_count: int = Field(default=30, ge=0, le=100000)
    requests_per_minute: int = Field(default=5, ge=0, le=100000)
    is_headless_user_agent: bool = False
    failed_logins_last_15m: int = Field(default=0, ge=0, le=100000)
    unrecognized_device_and_geo: bool = False
    password_reset_last_1h: bool = False


class CheckoutRequest(BaseModel):
    order_id: str = Field(
        min_length=3,
        max_length=40,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    user_id: str = Field(min_length=3, max_length=80)

    # Synthetic demo customer details only.
    buyer_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    phone: str = Field(min_length=3, max_length=40)
    address: str = Field(min_length=3, max_length=300)
    notes: str = Field(default="", max_length=2000)

    customer_country: str = Field(min_length=2, max_length=2)
    origin_country: str = Field(min_length=2, max_length=2)
    destination_country: str = Field(min_length=2, max_length=2)

    amount_usd: float = Field(gt=0, le=1_000_000)
    currency: str = Field(default="USD", min_length=3, max_length=3)

    # Demo only: PaymentTokenizer rejects any PAN except the published test PAN.
    card_number: str = Field(min_length=16, max_length=23)

    ip_country: str = Field(min_length=2, max_length=2)
    card_country: str = Field(min_length=2, max_length=2)
    tx_velocity_1h: int = Field(default=1, ge=0)
    account_age_days: int = Field(default=365, ge=0)
    is_vpn_or_tor: bool = False
    device_trust_score: float = Field(default=0.9, ge=0, le=1)
    shipping_billing_mismatch: bool = False
    telemetry: TelemetryInput = Field(default_factory=TelemetryInput)

    product_category: str = Field(
        default="CONSUMER_ELECTRONICS",
        min_length=2,
        max_length=80,
    )
    shipping_mode: str = Field(default="AIR_EXPRESS", min_length=2, max_length=40)
    has_export_license: bool = False


def _country(value: str) -> str:
    value = value.strip().upper()
    if not re.fullmatch(r"[A-Z]{2}", value):
        raise HTTPException(status_code=422, detail="Country must be a 2-letter code")
    return value


@app.get("/")
def dashboard():
    if not os.path.isfile(DASHBOARD_FILE):
        raise HTTPException(status_code=404, detail="Dashboard file not found")
    return FileResponse(DASHBOARD_FILE)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "checkout_orchestrator",
    }


@app.post("/api/v1/checkout")
def checkout(
    request: CheckoutRequest,
    _: None = Depends(require_demo_api_key),
) -> dict[str, Any]:
    # 1. Fraud score. No name, address, card number, or email is sent to the
    # fraud model.
    fraud_payload = {
        "amount_usd": request.amount_usd,
        "ip_country": _country(request.ip_country),
        "card_country": _country(request.card_country),
        "tx_velocity_1h": request.tx_velocity_1h,
        "account_age_days": request.account_age_days,
        "is_vpn_or_tor": request.is_vpn_or_tor,
        "device_trust_score": request.device_trust_score,
        "shipping_billing_mismatch": request.shipping_billing_mismatch,
        "telemetry": request.telemetry.model_dump(),
    }

    try:
        fraud_result = fraud_service.evaluate_transaction(fraud_payload)
    except Exception as exc:
        # Fail closed: do not proceed to tokenization if fraud scoring fails.
        raise HTTPException(
            status_code=503,
            detail="Fraud assessment unavailable; checkout not processed",
        ) from exc

    if fraud_result["decision"] == "BLOCK_AND_ALERT":
        return {
            "order_id": request.order_id,
            "checkout_status": "BLOCKED_FRAUD_RISK",
            "fraud_assessment": fraud_result,
            "payment_token_created": False,
            "shipment_created": False,
        }

    # 2. Sanctions, tariff, and export-control checks.
    compliance_payload = {
        "order_id": request.order_id,
        "buyer_name": request.buyer_name,
        "origin_country": _country(request.origin_country),
        "destination_country": _country(request.destination_country),
        "product_category": request.product_category,
        "declared_value_usd": request.amount_usd,
        "shipping_mode": request.shipping_mode,
        "has_export_license": request.has_export_license,
    }

    compliance_result = compliance_service.validate_cross_border_trade(
        compliance_payload
    )

    if not compliance_result["is_compliant"]:
        return {
            "order_id": request.order_id,
            "checkout_status": "BLOCKED_TRADE_COMPLIANCE",
            "fraud_assessment": fraud_result,
            "trade_compliance": compliance_result,
            "payment_token_created": False,
            "shipment_created": False,
        }

    # Medium risk stops for a real step-up challenge. This prototype does not
    # implement OTP/3DS, so it must not pretend that authentication succeeded.
    if fraud_result["decision"] == "STEP_UP_AUTH":
        return {
            "order_id": request.order_id,
            "checkout_status": "STEP_UP_AUTH_REQUIRED",
            "next_action": "Complete a real provider 3DS/OTP challenge before payment",
            "fraud_assessment": fraud_result,
            "trade_compliance": compliance_result,
            "payment_token_created": False,
            "shipment_created": False,
        }

    # 3. Tokenize only the published test PAN. No charge or authorization occurs.
    try:
        token_result = payment_tokenizer.tokenize(request.card_number)
        fx_result = convert_currency(
            Decimal(str(request.amount_usd)),
            request.currency.upper(),
            "USD",
        )
    except (TokenizationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # 4. Save synthetic customer information to the local regional simulation.
    try:
        privacy_result = privacy_store.save_customer_order(
            {
                "user_id": request.user_id,
                "country_code": _country(request.customer_country),
                "customer_name": request.buyer_name,
                "email": request.email,
                "phone": request.phone,
                "address": request.address,
                "notes": request.notes,
                "amount_usd": request.amount_usd,
            }
        )
    except RegionRoutingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # 5. Shipment creation is optional and best-effort. It must not make a
    # checkout claim that a real shipment exists if the Fabric bridge is down.
    shipment_id = f"SHIP-{request.order_id}"
    shipment_result: dict[str, Any] = {
        "status": "PENDING",
        "shipment_id": shipment_id,
        "detail": "Fabric bridge is not configured; run Phase 5 separately",
    }

    if FABRIC_BRIDGE_URL:
        try:
            response = httpx.post(
                f"{FABRIC_BRIDGE_URL}/api/v1/shipments",
                json={
                    "shipment_id": shipment_id,
                    "origin": _country(request.origin_country),
                    "destination": _country(request.destination_country),
                    "custodian": "GlobalTradeOrchestrator",
                },
                timeout=65,
            )
            if response.is_success:
                shipment_result = {
                    "status": "CREATED_IN_FABRIC_TEST_NETWORK",
                    "shipment_id": shipment_id,
                }
            else:
                shipment_result = {
                    "status": "PENDING_RETRY",
                    "shipment_id": shipment_id,
                    "detail": "Fabric bridge returned a non-success response",
                }
        except httpx.HTTPError:
            shipment_result = {
                "status": "PENDING_RETRY",
                "shipment_id": shipment_id,
                "detail": "Fabric bridge unavailable; no shipment confirmation",
            }

    return {
        "order_id": request.order_id,
        "checkout_status": "DEMO_ORDER_ACCEPTED",
        "payment": {
            "status": "TOKENIZED_PENDING_PROVIDER_AUTHORIZATION",
            "payment_token": token_result["payment_token"],
            "masked_card": token_result["masked_card"],
            "card_brand": token_result["card_brand"],
            "currency_conversion_demo": fx_result,
            "notice": "No payment was authorized, settled, or charged.",
        },
        "fraud_assessment": fraud_result,
        "trade_compliance": compliance_result,
        "privacy": {
            "region_route": privacy_result["region_route"],
            "analytics_pii_handling":
                privacy_result["analytics_pii_handling"],
        },
        "shipment": shipment_result,
    }
