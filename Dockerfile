FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       ca-certificates \
       curl \
       libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install -r /app/requirements.txt

# Presidio uses this English spaCy model in this demo.
RUN python -m spacy download en_core_web_sm

COPY . /app

# Training is reproducible from synthetic data; no model is downloaded.
RUN python -m fraud_engine.generate_data \
    && python -m fraud_engine.train_fraud_model \
    && python -m fraud_engine.fake_review_detector

RUN mkdir -p \
      /app/payment_vault/data \
      /app/privacy_governance/data \
      /app/iot_logistics/data \
      /app/compliance_engine/customs_docs \
    && useradd --system --uid 10001 --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "orchestrator.checkout_api:app", "--host", "0.0.0.0", "--port", "8000"]
