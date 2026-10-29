import httpx

from app.config import COMPLIANCE_URL, FRAUD_URL


def _call(url, payload, default, fallback):
    if not url:
        return default
    try:
        r = httpx.post(url, json=payload, timeout=5.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        return fallback


def fraud_score(payload: dict) -> dict:
    return _call(
        FRAUD_URL,
        payload,
        {"decision": "allow", "score": 0.0},
        {"decision": "review", "score": None, "reason": "fraud_service_unavailable"},
    )


def compliance_check(payload: dict) -> dict:
    return _call(
        COMPLIANCE_URL,
        payload,
        {"decision": "approved", "reasons": []},
        {"decision": "review", "reasons": ["compliance_service_unavailable"]},
    )