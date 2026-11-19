from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from payment_vault.auth import issue_demo_jwt, require_payment_jwt
from payment_vault.currency import convert_currency
from payment_vault.tokenizer import PaymentTokenizer, TokenizationError


app = FastAPI(
    title="Payment Tokenization Demo",
    version="1.0.0",
    description=(
        "Educational-only test-card tokenization demo. "
        "It does not process or charge payments and is not PCI-DSS certified."
    ),
)

tokenizer = PaymentTokenizer()


class PaymentRequest(BaseModel):
    transaction_id: str = Field(min_length=3, max_length=64)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    card_number: str = Field(
        ...,
        min_length=16,
        max_length=23,
        description="Demo accepts only the published test PAN; never send a real PAN.",
    )
    ip_country: str = Field(min_length=2, max_length=2)
    billing_country: str = Field(min_length=2, max_length=2)

    @field_validator("currency", "ip_country", "billing_country")
    @classmethod
    def uppercase_codes(cls, value: str) -> str:
        return value.upper()

    @field_validator("card_number")
    @classmethod
    def normalise_card_number(cls, value: str) -> str:
        return value.replace(" ", "").replace("-", "")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "payment_tokenization_demo"}


@app.post("/api/v1/auth/token")
def create_token(auth_result: dict[str, Any] = Depends(issue_demo_jwt)):
    return auth_result


@app.post("/api/v1/payment/process")
def process_demo_payment(
    request: PaymentRequest,
    claims: dict[str, Any] = Depends(require_payment_jwt),
):
    # Do not log or return request.card_number.
    try:
        token_result = tokenizer.tokenize(request.card_number)
        fx_result = convert_currency(
            request.amount,
            request.currency,
            "USD",
        )
    except TokenizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (ValueError, InvalidOperation) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    country_mismatch = request.ip_country != request.billing_country
    risk_indicators = (
        ["IP_BILLING_COUNTRY_MISMATCH"] if country_mismatch else []
    )

    # This is NOT a card authorization or payment charge.
    return {
        "transaction_id": request.transaction_id,
        "payment_status": "TOKENIZED_PENDING_PROVIDER_AUTHORIZATION",
        "payment_token": token_result["payment_token"],
        "masked_card": token_result["masked_card"],
        "card_brand": token_result["card_brand"],
        "amount": str(request.amount),
        "currency": request.currency,
        "demo_usd_conversion": fx_result,
        "risk_indicators": risk_indicators,
        "authenticated_subject": claims["sub"],
        "notice": (
            "Demo only: no payment was authorized, settled, or charged. "
            "Use a payment provider for real card processing."
        ),
    }
