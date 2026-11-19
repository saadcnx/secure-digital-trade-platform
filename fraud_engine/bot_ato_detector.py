from typing import Dict, Any, List

class BehavioralSecurityAnalyzer:
    """
    Detects Automated Bot Abuse and Account Takeover (ATO) attacks
    using behavioral biometrics and session telemetry.
    """

    @staticmethod
    def evaluate_session(telemetry: Dict[str, Any]) -> Dict[str, Any]:
        risk_points = 0.0
        flags: List[str] = []

        # 1. Bot Telemetry Checks (Keystroke/Mouse/Speed)
        checkout_seconds = telemetry.get("checkout_duration_sec", 25.0)
        mouse_events = telemetry.get("mouse_movement_count", 50)
        requests_per_min = telemetry.get("requests_per_minute", 5)
        headless_browser = telemetry.get("is_headless_user_agent", False)

        if checkout_seconds < 3.0:
            risk_points += 0.45
            flags.append("SUPERHUMAN_CHECKOUT_SPEED (<3s)")

        if mouse_events < 3:
            risk_points += 0.35
            flags.append("ZERO_HUMAN_MOUSE_INTERACTION")

        if requests_per_min > 40 or headless_browser:
            risk_points += 0.50
            flags.append("AUTOMATED_SCRAPER_OR_BOT_SIGNATURE")

        # 2. Account Takeover (ATO) Checks
        failed_logins = telemetry.get("failed_logins_last_15m", 0)
        new_device_and_ip = telemetry.get("unrecognized_device_and_geo", False)
        password_changed_recently = telemetry.get("password_reset_last_1h", False)

        if failed_logins >= 5:
            risk_points += 0.45
            flags.append(f"CREDENTIAL_STUFFING_DETECTED ({failed_logins} failed logins)")

        if new_device_and_ip and password_changed_recently:
            risk_points += 0.55
            flags.append("HIGH_RISK_ACCOUNT_TAKEOVER_PATTERN (New Geo + Recent Password Change)")

        behavior_score = min(round(risk_points, 3), 1.0)
        is_bot_or_ato = behavior_score >= 0.60

        return {
            "behavioral_risk_score": behavior_score,
            "is_bot_or_ato": is_bot_or_ato,
            "behavioral_flags": flags
        }
