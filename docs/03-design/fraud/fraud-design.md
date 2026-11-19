# Phase 3A: Fraud Detection Design

**Roles:** ML/Fraud Engineer (lead), Architect, DevSecOps (serving)
**Requirements:** FR-FRD-01 to FR-FRD-07, NFR-01, NFR-11, NFR-12
**ADRs:** ADR-0004 (lawful basis), ADR-0009 (Fabric custody evidence)
**Risks:** R-04 (model drift/poisoning), R-05 (false positives)

## 1. Tasks

### 1.1 Taxonomy and labels

| Class | Description | Primary label | Proxy label (faster) |
|---|---|---|---|
| Payment fraud | Unauthorised transaction, stolen card | Chargeback (30–120 day lag) | 3DS failure, PSP decline reason |
| Account takeover (ATO) | Credential stuffing, session hijack | Analyst-confirmed ATO case | Impossible-travel alert, breached-password hit |
| Bots / card testing | High-velocity enumeration | Velocity rule fire + analyst review | Auth-failure burst per device/IP |
| Fake reviews | Coordinated inauthentic content | Analyst moderation decision | Embedding-similarity flag |

Chargeback labels arrive 30–120 days late. Until they mature, use analyst decisions and 3DS failures as faster proxy labels. Document the label-source mix in the model card.

### 1.2 Synthetic data generator

Faker for demographic and catalogue fields. Injected attack patterns:

- Card testing: 50–200 auth attempts per device within 5 minutes, mixed BINs.
- ATO: login from new device + new country + order within 10 minutes.
- Bust-out: many small orders then one large, escalating over 72 h.
- Fake review burst: 20+ reviews on one product from accounts < 7 days old.

**No real PII or PAN.** Seeded so runs are reproducible.

### 1.3 Features (computed per cell)

| Group | Feature | Window | Source |
|---|---|---|---|
| Velocity | Attempts per device | 1 min, 1 h, 24 h | Kafka stream |
| Velocity | Attempts per IP | 1 min, 1 h, 24 h | Kafka stream |
| Velocity | Attempts per card-token | 1 min, 1 h, 24 h | Token store + Kafka |
| Velocity | Attempts per email-hash | 1 min, 1 h, 24 h | Kafka stream |
| Device/geo | Fingerprint age (days) | point-in-time | Device registry |
| Device/geo | Impossible travel (km/h) | point-in-time | Geo + last login |
| Device/geo | IP vs billing country mismatch | point-in-time | Geo |
| Graph | Accounts sharing a device | expanding | Graph store |
| Graph | Accounts sharing a token | expanding | Graph store |
| Behaviour | Login event sequence hash | session | Kafka |
| Behaviour | Cart event sequence hash | session | Kafka |
| Behaviour | Time-to-checkout (seconds) | session | Checkout service |

All identifiers are **salted hashes**. No PAN or C3 data enters the feature store.

### 1.4 Models

| Model | Role | Framework | Output |
|---|---|---|---|
| XGBoost | Primary tabular scorer | Native / ONNX | Calibrated P(fraud) |
| TensorFlow autoencoder | Behavioural anomaly (ATO, bot) | TF Serving (in-process) | Anomaly score |
| scikit-learn Isolation Forest | Baseline + calibration | joblib in-process | Calibration offset |
| Isotonic regression | Score calibration | scikit-learn | Calibrated score |

XGBoost is the foundation. TensorFlow adds an anomaly signal where sequences matter. Deep learning is not the foundation.

### 1.5 Decision engine

Inputs: calibrated score, rule hits, context (order value, customer tenure, corridor).

| Tier | Condition | Action |
|---|---|---|
| Allow | P(fraud) × loss < friction cost × 0.5 | Proceed |
| Step-up | P(fraud) × loss between 0.5× and 1.5× friction cost | 3DS / SCA challenge |
| Review | P(fraud) × loss between 1.5× and 3× friction cost | Manual queue, order held |
| Block | P(fraud) × loss > 3× friction cost | Reject, reason code, appeal path |

Thresholds are **cost-based, not an arbitrary 0.8**. They need honest cost estimates — register them as assumptions.

### 1.6 Reason codes (NFR-12, Art. 22)

Top-3 SHAP features mapped to fixed codes:

| Code | Feature | Plain-language message |
|---|---|---|
| `VELOCITY_HIGH` | Velocity per device > threshold | "Too many attempts from this device" |
| `GEO_MISMATCH` | IP/billing country mismatch | "Location doesn't match your billing address" |
| `NEW_DEVICE` | Fingerprint age < 1 day | "New device on this account" |
| `GRAPH_CLUSTER` | Account shares device/token with flagged accounts | "Account linked to a flagged account" |
| `SEQ_ANOMALY` | Behaviour sequence anomaly | "Unusual activity pattern" |
| `BIN_HIGH_RISK` | High-risk BIN corridor | "Card issuer region needs extra verification" |

100% of non-allow decisions carry reason codes. Automated check in CI.

### 1.7 Fake reviews (async only)

Text embeddings (sentence-transformers) + reviewer-product graph. Flags content for moderation. **Never blocks checkout.** Flag-then-review: harmful reviews live briefly.

### 1.8 Monitoring

| Metric | Alert threshold | Action |
|---|---|---|
| PSI per feature | > 0.2 | Drift alert, shadow challenger |
| Score distribution shift | KS test p < 0.01 | Investigate |
| Fallback rate | > 5% of decisions | Alert, review fallback losses |
| Shadow (challenger) disagreement | > 10% | Review promotion readiness |
| False-positive rate by country/segment | > 2× baseline | Bias check before promotion |

## 2. Decisions and Trade-offs

| Decision | Choice | Why | Trade-off |
|---|---|---|---|
| Thresholds | Cost-based: act when P(fraud) × loss > friction cost | Ties to BD-1 and conversion | Needs honest cost estimates (assumptions) |
| Serving | XGBoost in-process (ONNX or native) | Saves network hop (~10–20 ms) | Model updates mean redeploy or hot-reload |
| Online features | Redis fed by stream job; Feast for definitions | Same features in training and serving, no skew | Extra infrastructure. Fallback: compute in stream job only (ADR-0009 trigger) |
| Deep learning | Only for behaviour anomaly, as additional signal | Latency and explainability stay with XGBoost | Ensemble complexity |
| Retraining | Weekly scheduled + drift-triggered, champion/challenger | Fraud patterns shift fast | Label delay means recent data under-labelled |
| Fake reviews | Async, flag-then-review | Zero checkout latency impact | Harmful reviews live briefly |

### Latency budget (p99 150 ms, 100 ms hard timeout)

| Step | Budget |
|---|---|
| Network and gRPC | 15 ms |
| Redis feature fetch | 20 ms |
| Model inference (XGBoost + light TF) | 30 ms |
| Rules and decision | 10 ms |
| Margin | 25 ms |
| **Total** | **~100 ms** |

## 3. Diagram: Fraud Component View (C4 L3)

See `docs/diagrams/3.1-fraud-components.drawio`.

- **Left:** Checkout → Risk Decision Service (Feature Fetcher, Model Runner, Rules Engine, Decision and Reason-code builder, Fallback Rules).
- **Right:** Redis (online), Kafka, Stream Processor (feature computation), Feast registry.
- **Bottom (offline loop, different colour):** Kafka → Data lake → Training job → MLflow registry → signed model artefact → Risk Service. Case Management feeds labels back to the lake.

## 4. Security, Privacy, and Controls

- Features are pseudonymised (salted hashes). No PAN or C3 data enters the feature store.
- Model artefacts are signed. Registry is write-restricted (counters poisoning, R-04).
- Every decision logged with model version, rule version, and reason codes (audit).
- Bias check: compare false-positive rate by country and segment before promotion.
- Art. 22: block decisions have a review and appeal path (ADR-0004).

## 5. Failure Scenarios

| Scenario | Behaviour |
|---|---|
| Redis down | Missing-feature defaults + stricter rules tier, alert |
| Model drift | PSI alert, auto-shadow challenger, one-click rollback |
| Label poisoning or attack | Rate limits at edge, anomaly check on training data |
| Scorer timeout | 100 ms cutoff, fallback rules by order value (ADR-0004) |

## 6. Examiner Questions

**Q: Why XGBoost, not deep learning?**
Strong: "Tabular transaction data suits gradient boosting, inference is fast, and SHAP gives reason codes for Art. 22. TensorFlow adds an anomaly signal where sequences matter, but is not the foundation."
Weak: "Deep learning is more advanced."

**Q: How do you choose the block threshold?**
Strong: "Expected-cost based: block when expected fraud loss exceeds friction and lost-sale cost. I use step-up as the middle tier, and I review the threshold when chargeback data matures."
Weak: "0.5" or "whatever gives the best accuracy."

**Q: How do you evaluate with delayed labels and imbalance?**
Strong: "I use precision-recall, not accuracy, and cost-weighted metrics. I time-split the data to avoid leakage, use proxy labels for speed, and say plainly that my metrics come from synthetic data."
Weak: "We use accuracy."