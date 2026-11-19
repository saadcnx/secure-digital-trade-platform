from decimal import Decimal, ROUND_HALF_UP


# Educational sample rates only: units of currency per 1 USD.
# These are not live or suitable for settling real payments.
DEMO_RATES_PER_USD = {
    "USD": Decimal("1.00"),
    "EUR": Decimal("0.92"),
    "GBP": Decimal("0.79"),
    "PKR": Decimal("278.00"),
}


def convert_currency(amount: Decimal, source: str, target: str) -> dict:
    source = source.upper()
    target = target.upper()

    if source not in DEMO_RATES_PER_USD:
        raise ValueError(f"Unsupported demo currency: {source}")
    if target not in DEMO_RATES_PER_USD:
        raise ValueError(f"Unsupported demo currency: {target}")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    # Convert source currency -> USD -> target currency.
    amount_usd = amount / DEMO_RATES_PER_USD[source]
    converted = amount_usd * DEMO_RATES_PER_USD[target]

    return {
        "source_currency": source,
        "source_amount": str(amount.quantize(Decimal("0.01"))),
        "target_currency": target,
        "converted_amount": str(
            converted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        ),
        "rate_source": "STATIC_EDUCATIONAL_DEMO_RATES",
    }
