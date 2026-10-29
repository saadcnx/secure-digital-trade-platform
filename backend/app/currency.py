from decimal import ROUND_HALF_UP, Decimal

RATES = {
    "USD": Decimal("1"),
    "EUR": Decimal("0.92"),
    "GBP": Decimal("0.79"),
    "PKR": Decimal("280"),
}

CENT = Decimal("0.01")


def convert(amount, src: str, dst: str) -> Decimal:
    amount = Decimal(amount)
    if src != dst:
        amount = amount / RATES[src] * RATES[dst]
    return amount.quantize(CENT, ROUND_HALF_UP)