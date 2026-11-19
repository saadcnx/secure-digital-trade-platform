from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any
from compliance_engine.service import TradeComplianceService

app = FastAPI(
    title="Cross-Border Trade Compliance & Sanctions Engine",
    version="1.0.0",
    description="Automated OFAC/UN Fuzzy Sanctions Screening, WCO HS-Code Tariffs, Export Controls & Digital CN23 Customs Docs"
)

compliance_service = TradeComplianceService()

class TradeComplianceRequest(BaseModel):
    order_id: str = Field(..., example="ORD-7001")
    buyer_name: str = Field(..., example="Muhammad Saad Khan")
    origin_country: str = Field(default="US", min_length=2, max_length=2)
    destination_country: str = Field(..., min_length=2, max_length=2, example="GB")
    product_category: str = Field(..., example="CONSUMER_ELECTRONICS")
    declared_value_usd: float = Field(..., gt=0, example=450.00)
    shipping_mode: str = Field(default="AIR_EXPRESS", example="AIR_EXPRESS")
    has_export_license: bool = False

@app.get("/health")
def health_check() -> Dict[str, Any]:
    return {"status": "healthy", "service": "compliance_engine"}

@app.post("/api/v1/compliance/validate")
def validate_trade(req: TradeComplianceRequest) -> Dict[str, Any]:
    return compliance_service.validate_cross_border_trade(req.model_dump())
