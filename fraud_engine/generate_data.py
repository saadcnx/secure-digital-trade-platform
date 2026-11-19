import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "transactions.csv"

def generate_synthetic_transactions(n_samples: int = 6000) -> pd.DataFrame:
    np.random.seed(42)

    # Realistic E-Commerce & Cross-Border Features
    amount_usd = np.round(np.random.exponential(scale=250, size=n_samples) + 10, 2)
    country_mismatch = np.random.choice([0, 1], size=n_samples, p=[0.82, 0.18]) # IP Country != Card Country
    tx_velocity_1h = np.random.poisson(lam=1.5, size=n_samples)                  # Orders in last 1 hour
    account_age_days = np.random.randint(1, 1500, size=n_samples)               # Customer account age
    is_vpn_or_tor = np.random.choice([0, 1], size=n_samples, p=[0.90, 0.10])    # Anonymous proxy/VPN
    device_trust_score = np.round(np.random.uniform(0.1, 1.0, size=n_samples), 2)
    shipping_billing_mismatch = np.random.choice([0, 1], size=n_samples, p=[0.85, 0.15])

    # Calculate underlying fraud log-odds (Realistic Industry Patterns)
    risk_signal = (
        (amount_usd > 1200) * 1.8 +
        (country_mismatch == 1) * 1.6 +
        (tx_velocity_1h >= 5) * 2.0 +
        (account_age_days < 7) * 1.3 +
        (is_vpn_or_tor == 1) * 2.1 +
        (device_trust_score < 0.35) * 1.5 +
        (shipping_billing_mismatch == 1) * 0.9 - 3.2
    )

    # Add slight noise so ML learns patterns, not rigid rules
    noise = np.random.normal(0, 0.4, size=n_samples)
    prob = 1 / (1 + np.exp(-(risk_signal + noise)))
    is_fraud = (prob > 0.55).astype(int)

    df = pd.DataFrame({
        "amount_usd": amount_usd,
        "country_mismatch": country_mismatch,
        "tx_velocity_1h": tx_velocity_1h,
        "account_age_days": account_age_days,
        "is_vpn_or_tor": is_vpn_or_tor,
        "device_trust_score": device_trust_score,
        "shipping_billing_mismatch": shipping_billing_mismatch,
        "is_fraud": is_fraud
    })
    return df

if __name__ == "__main__":
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = generate_synthetic_transactions(6000)
    df.to_csv(DATA_PATH, index=False)
    fraud_rate = df["is_fraud"].mean() * 100
    print(f"✅ Generated {len(df)} transactions at: {DATA_PATH}")
    print(f"📊 Fraud Distribution: {df['is_fraud'].sum()} Fraudulent ({fraud_rate:.2f}%) | {len(df) - df['is_fraud'].sum()} Legitimate")
