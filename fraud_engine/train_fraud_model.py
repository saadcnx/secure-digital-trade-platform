import joblib
import pandas as pd
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "transactions.csv"
MODEL_PATH = BASE_DIR / "models" / "xgb_payment_fraud.pkl"

FEATURE_COLUMNS = [
    "amount_usd",
    "country_mismatch",
    "tx_velocity_1h",
    "account_age_days",
    "is_vpn_or_tor",
    "device_trust_score",
    "shipping_billing_mismatch",
]

def train_model():
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLUMNS]
    y = df["is_fraud"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Handle class imbalance using scale_pos_weight (Industry Best Practice)
    scale_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

    model = XGBClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.08,
        scale_pos_weight=scale_weight,
        eval_metric="logloss",
        random_state=42
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURE_COLUMNS, "roc_auc": round(float(auc), 4)}, MODEL_PATH)

    print("✅ XGBoost Fraud Model Trained & Saved:", MODEL_PATH)
    print(f"🎯 ROC-AUC Score: {auc:.4f}\n")
    print("📋 Classification Report:\n", classification_report(y_test, y_pred))

if __name__ == "__main__":
    train_model()
