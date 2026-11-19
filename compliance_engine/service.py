from typing import Dict, Any
from compliance_engine.sanctions_screener import SanctionsScreener
from compliance_engine.tariff_classifier import TariffClassifier
from compliance_engine.jurisdiction_policy import JurisdictionPolicyEngine
from compliance_engine.customs_doc_generator import CustomsDocumentGenerator

class TradeComplianceService:
    def __init__(self):
        self.screener = SanctionsScreener(match_threshold=84.0)
        self.tariff_engine = TariffClassifier()

    def validate_cross_border_trade(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        order_id = payload.get("order_id", "ORD-UNKNOWN")
        buyer_name = payload.get("buyer_name", "Anonymous")
        origin = payload.get("origin_country", "US")
        destination = payload.get("destination_country", "GB")
        category = payload.get("product_category", "CONSUMER_ELECTRONICS")
        value_usd = float(payload.get("declared_value_usd", 100.0))
        shipping_mode = payload.get("shipping_mode", "AIR_EXPRESS")
        has_license = bool(payload.get("has_export_license", False))

        # 1. Sanctions & Denied Party Screening
        sanctions_res = self.screener.screen_party_and_route(
            buyer_name=buyer_name,
            origin_country=origin,
            destination_country=destination
        )

        # 2. WCO HS-Code & Landed Duty/VAT Calculation
        tariff_res = self.tariff_engine.calculate_landed_cost(
            product_category=category,
            declared_value_usd=value_usd,
            destination_country=destination
        )

        # 3. Import/Export Jurisdiction Policy Validation
        policy_res = JurisdictionPolicyEngine.evaluate_regulations(
            product_category=category,
            eccn_code=tariff_res["export_control_eccn"],
            destination_country=destination,
            shipping_mode=shipping_mode,
            has_export_license=has_license
        )

        all_violations = sanctions_res["sanctions_violations"] + policy_res["policy_violations"]
        is_approved = len(all_violations) == 0

        # 4. Issue Automated Customs Document ONLY if trade is compliant
        customs_doc = None
        if is_approved:
            customs_doc = CustomsDocumentGenerator.issue_customs_declaration(
                order_id=order_id,
                buyer_name=buyer_name,
                origin_country=origin,
                destination_country=destination,
                shipping_mode=shipping_mode,
                tariff_summary=tariff_res,
                handling_controls=policy_res["mandatory_handling_controls"]
            )
            compliance_status = "COMPLIANT_CLEARED_FOR_EXPORT"
        else:
            compliance_status = "HOLD_REGULATORY_COMPLIANCE_BLOCK"

        return {
            "order_id": order_id,
            "compliance_status": compliance_status,
            "is_compliant": is_approved,
            "sanctions_screening": sanctions_res,
            "tariff_and_duties": tariff_res,
            "jurisdiction_governance": policy_res,
            "electronic_customs_declaration": customs_doc
        }
