# Capability Map

## Bands

Five horizontal bands. Each holds 4–6 capability boxes. Colour by **build / adopt / buy**.

### 1. Fraud & Trust
- Real-time scoring
- Account takeover detection
- Bot & card-testing defence
- Review integrity
- Reason codes & explainability
- Analyst feedback loop

### 2. Trade Compliance
- Sanctions screening
- HS classification
- Document validation
- Rules management (policy-as-code)
- Case review

### 3. Supply Chain Visibility
- Custody ledger
- IoT ingestion (GPS, temperature)
- Route & dwell anomaly
- Counterfeit signals
- Per-party visibility

### 4. Payments
- Token abstraction
- PSP adapter
- 3-D Secure / SCA step-up
- Multi-currency & FX
- Idempotency

### 5. Platform & Governance
- Identity (Keycloak)
- Secrets (Vault)
- Observability (Prometheus, Grafana, OTel)
- DevSecOps (Argo CD, scanning)
- Privacy (DSAR, retention)
- Policy (OPA)

## Colouring rule

- **Build** (own code): Risk Decision, Token Abstraction, Compliance policy logic.
- **Adopt** (open-source, self-managed): Kafka, Keycloak, Vault, Istio, Prometheus, Fabric, XGBoost, Feast, MLflow.
- **Buy / integrate**: PSP, sanctions feeds, 3-D Secure, carrier connectivity.

See `../build-adopt-buy/build-adopt-buy.md` for full rationale.