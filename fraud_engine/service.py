import joblib
import pandas as pd
from pathlib import Path
from typing import Dict, Any
from fraud_engine.bot_ato_detector import BehavioralSecurityAnalyzer
from fraud_engine.fake_review_detector import ReviewFraudAnalyzer

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "xgb_payment_fraud.pkl"

class FraudDetectionService:
    def __init__(self):
        bundle = joblib.load(MODEL_PATH)
        self.xgb_model = bundle["model"]
        self.features = bundle["features"]
        self.model_auc = bundle["roc_auc"]
        self.behavior_analyzer = BehavioralSecurityAnalyzer()
        self.review_analyzer = ReviewFraudAnalyzer()

    def evaluate_transaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Run XGBoost Payment Fraud Scoring
        ip_country = payload.get("ip_country", "US")
        card_country = payload.get("card_country", "US")
        country_mismatch = 1 if ip_country != card_country else 0

        row = pd.DataFrame([{
            "amount_usd": float(payload.get("amount_usd", 50.0)),
            "country_mismatch": country_mismatch,
            "tx_velocity_1h": int(payload.get("tx_velocity_1h", 1)),
            "account_age_days": int(payload.get("account_age_days", 180)),
            "is_vpn_or_tor": int(bool(payload.get("is_vpn_or_tor", False))),
            "device_trust_score": float(payload.get("device_trust_score", 0.9)),
            "shipping_billing_mismatch": int(bool(payload.get("shipping_billing_mismatch", False))),
        }])

        ml_prob = float(self.xgb_model.predict_proba(row[self.features])[0][1])

        # 2. Run Behavioral Bot & Account Takeover (ATO) Analysis
        behavior_res = self.behavior_analyzer.evaluate_session(payload.get("telemetry", {}))
        beh_score = behavior_res["behavioral_risk_score"]

        # 3. Ensemble Risk Aggregation (Weighted ML + Behavioral Telemetry)
        combined_score = round(min(max(ml_prob, (ml_prob * 0.65) + (beh_score * 0.55)), 1.0), 4)

        # Explainable Risk Reasons (Crucial for Compliance & SOC Analysts)
        reasons = list(behavior_res["behavioral_flags"])
        if country_mismatch:
            reasons.append(f"CROSS_BORDER_IP_CARD_MISMATCH ({ip_country} vs {card_country})")
        if payload.get("is_vpn_or_tor"):
            reasons.append("ANONYMOUS_VPN_OR_TOR_EXIT_NODE")
        if float(payload.get("amount_usd", 0)) > 1200:
            reasons.append("HIGH_VALUE_CROSS_BORDER_ORDER")
        if int(payload.get("tx_velocity_1h", 1)) >= 5:
            reasons.append("ABNORMAL_TRANSACTION_VELOCITY")

        # 4. Automated Fraud Response Workflow (Step 13)
        if behavior_res["is_bot_or_ato"] or combined_score >= 0.75:
            decision = "BLOCK_AND_ALERT"
            workflow_action = "REJECT_CHECKOUT_TRIGGER_SOC_SIEM_ALERT"
        elif combined_score >= 0.40:
            decision = "STEP_UP_AUTH"
            workflow_action = "CHALLENGE_3DS2_AND_OTP_VERIFICATION"
        else:
            decision = "ALLOW"
            workflow_action = "PROCEED_TO_TRADE_COMPLIANCE_AND_SETTLEMENT"

        return {
            "decision": decision,
            "automated_workflow": workflow_action,
            "combined_risk_score": combined_score,
            "ml_payment_fraud_probability": round(ml_prob, 4),
            "behavioral_risk_score": beh_score,
            "is_bot_or_ato": behavior_res["is_bot_or_ato"],
            "risk_indicators": reasons,
            "model_metadata": {
                "engine": "XGBoost + Behavioral Telemetry",
                "validation_roc_auc": self.model_auc
            }
        }
