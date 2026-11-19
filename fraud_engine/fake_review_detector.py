import joblib
from pathlib import Path
from typing import Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

BASE_DIR = Path(__file__).resolve().parent
REVIEW_MODEL_PATH = BASE_DIR / "models" / "nlp_fake_review.pkl"

def train_review_model():
    # Curated Training Corpus: Genuine vs Spam/Bot Reviews
    texts = [
        # Genuine Reviews (0)
        "Product arrived on time and packaging was solid. Works as advertised.",
        "Good quality cotton shirt, size fits slightly small but overall happy.",
        "Battery life lasts around 8 hours. Decent value for cross-border shipping.",
        "Customs clearance took two extra days, however customer support was helpful.",
        "The bluetooth speaker has clear audio, bass is average for the price.",
        "Solid build quality, used it for three weeks without any overheating issues.",
        "Fast international delivery, adapter plug included in the box.",
        "Screen resolution is sharp, though the stand feels a bit plastic.",
        "Authentic perfume, batch code verified properly. Will order again.",
        "Good winter jacket, zippers are sturdy and keeps warm in cold weather.",
        # Fake / Bot / Incentivized Reviews (1)
        "BEST PRODUCT EVER BUY NOW 100% GUARANTEED CLICK LINK FREE GIFT!!!",
        "Amazing amazing amazing five stars best seller whatsapp +123456 for discount",
        "Great item!! Great item!! Must buy immediately cheap price promo code WIN99",
        "I received free cashback to write 5 star review best miracle product ever!!",
        "SUPERB A+++++ TOP SELLER FASTEST MONEY BACK CLICK PROFILE FOR CRYPTO DEAL",
        "Buy cheap luxury replica watches here best store 1000% legit telegram link",
        "Five stars five stars awesome miracle cure instant results buy 10 pieces now!!",
        "Best store in universe!! DM for free coupon giveaway 5/5 stars guaranteed!!",
        "100% ORIGINAL SUPER DISCOUNT HURRY UP LIMITED STOCK CLICK URL NOW",
        "Wow wow best gadget in history changed my life overnight buy immediately!!!"
    ]
    labels = [0]*10 + [1]*10

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
        ("clf", LogisticRegression(random_state=42))
    ])

    pipeline.fit(texts, labels)
    REVIEW_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, REVIEW_MODEL_PATH)
    print(f"✅ NLP Fake Review Model Trained & Saved: {REVIEW_MODEL_PATH}")

class ReviewFraudAnalyzer:
    def __init__(self):
        if not REVIEW_MODEL_PATH.exists():
            train_review_model()
        self.pipeline = joblib.load(REVIEW_MODEL_PATH)

    def analyze_review(self, review_text: str, verified_purchase: bool, duplicate_burst_count: int = 1) -> Dict[str, Any]:
        nlp_prob = float(self.pipeline.predict_proba([review_text])[0][1])
        flags = []

        # Combine ML NLP probability with marketplace metadata heuristics
        meta_penalty = 0.0
        if not verified_purchase:
            meta_penalty += 0.20
            flags.append("UNVERIFIED_PURCHASE")
        if duplicate_burst_count >= 3:
            meta_penalty += 0.35
            flags.append("REVIEW_BOMBING_BURST_DETECTED")
        if sum(1 for c in review_text if c.isupper()) > max(len(review_text) * 0.4, 10):
            meta_penalty += 0.20
            flags.append("EXCESSIVE_CAPS_SPAM_PATTERN")

        final_score = min(round(nlp_prob * 0.75 + meta_penalty, 3), 1.0)
        status = "QUARANTINE_FAKE_REVIEW" if final_score >= 0.55 else "PUBLISH_GENUINE"

        return {
            "nlp_spam_probability": round(nlp_prob, 3),
            "combined_fake_score": final_score,
            "moderation_action": status,
            "flags": flags
        }

if __name__ == "__main__":
    train_review_model()
