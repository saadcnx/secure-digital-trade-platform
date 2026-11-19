import pytest
from fastapi import HTTPException

from orchestrator import checkout_api
from orchestrator.checkout_api import CheckoutRequest


def test_checkout_fails_closed_if_fraud_service_fails(monkeypatch):
    def fail_fraud(_payload):
        raise RuntimeError("simulated fraud service outage")

    monkeypatch.setattr(
        checkout_api.fraud_service,
        "evaluate_transaction",
        fail_fraud,
    )

    request = CheckoutRequest(
        order_id="FAILURE-TEST-001",
        user_id="demo-failure-user",
        buyer_name="Demo User",
        email="demo.failure@example.com",
        phone="+1 202 555 0199",
        address="1 Demo Test Street",
        customer_country="GB",
        origin_country="US",
        destination_country="GB",
        amount_usd=25,
        currency="USD",
        card_number="4242424242424242",
        ip_country="GB",
        card_country="GB",
    )

    with pytest.raises(HTTPException) as error:
        checkout_api.checkout(request, None)

    assert error.value.status_code == 503
    assert "Fraud assessment unavailable" in error.value.detail
