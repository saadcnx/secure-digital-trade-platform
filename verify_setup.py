import fastapi
import xgboost
import sklearn
import cryptography
import rapidfuzz
import paho.mqtt.client as mqtt
from presidio_analyzer import AnalyzerEngine

print("✅ 1. FastAPI Version:", fastapi.__version__)
print("✅ 2. XGBoost (Fraud AI) Version:", xgboost.__version__)
print("✅ 3. Scikit-Learn Version:", sklearn.__version__)
print("✅ 4. Cryptography (PCI-DSS) Version:", cryptography.__version__)
print("✅ 5. RapidFuzz (Sanctions Engine) Version:", rapidfuzz.__version__)
print("✅ 6. Paho-MQTT (IoT Logistics) Loaded Successfully!")

analyzer = AnalyzerEngine()
res = analyzer.analyze(text="Order by Muhammad Saad from London", entities=["PERSON", "LOCATION"], language="en")
print(f"✅ 7. Microsoft Presidio (GDPR Privacy) Detected {len(res)} PII Entities:", [r.entity_type for r in res])
print("\n🎉 ALL ENTERPRISE OPEN-SOURCE MODULES ARE 100% READY!")
