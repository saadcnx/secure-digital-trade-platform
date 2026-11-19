from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any
from fraud_engine.service import FraudDetectionService

app = FastAPI(
    title="AI Fraud Detection & Behavioral Security Microservice",
    version="1.0.0",
    description="Real-time XGBoost Payment Fraud, Bot/ATO Behavioral Analytics & NLP Fake Review Engine"
)

fraud_service = FraudDetectionService()

class TelemetryInput(BaseModel):
    checkout_duration_sec: float = 22.0
    mouse_movement_count: int = 45
    requests_per_minute: int = 4
    is_headless_user_agent: bool = False
    failed_logins_last_15m: int = 0
    unrecognized_device_and_geo: bool = False
    password_reset_last_1h: bool = False

class TransactionScoringRequest(BaseModel):
    transaction_id: str = Field(..., example="TXN-9001")
    amount_usd: float = Field(..., gt=0, example=120.50)
    ip_country: str = Field(..., example="GB")
    card_country: str = Field(..., example="GB")
    tx_velocity_1h: int = Field(default=1, ge=0)
    account_age_days: int = Field(default=365, ge=0)
    is_vpn_or_tor: bool = False
    device_trust_score: float = Field(default=0.92, ge=0.0, le=1.0)
    shipping_billing_mismatch: bool = False
    telemetry: TelemetryInput = TelemetryInput()

class ReviewCheckRequest(BaseModel):
    product_id: str = "PROD-442"
    review_text: str
    verified_purchase: bool = True
    duplicate_burst_count: int = 1

@app.get("/health")
def health_check() -> Dict[str, Any]:
    return {"status": "healthy", "service": "fraud_engine", "model_auc": fraud_service.model_auc}

@app.post("/api/v1/fraud/score")
def score_transaction(req: TransactionScoringRequest) -> Dict[str, Any]:
    result = fraud_service.evaluate_transaction(req.model_dump())
    return {"transaction_id": req.transaction_id, **result}

@app.post("/api/v1/fraud/review-check")
def check_review(req: ReviewCheckRequest) -> Dict[str, Any]:
    result = fraud_service.review_analyzer.analyze_review(
        review_text=req.review_text,
        verified_purchase=req.verified_purchase,
        duplicate_burst_count=req.duplicate_burst_count
    )
    return {"product_id": req.product_id, **result}
