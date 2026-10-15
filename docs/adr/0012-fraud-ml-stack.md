# ADR-0012: Fraud ML stack — gradient boosting core, deep learning where it earns its place

- **Status:** Accepted
- **Date / Owner:** Phase 2 / ML/Fraud Engineer

## Options considered

1. XGBoost only.
2. TensorFlow deep models only.
3. **XGBoost plus targeted TF/sklearn components.**

## Decision

Choose **option 3.**
- **XGBoost** as the primary tabular scorer (fast, well-understood on transactional data, supports SHAP-style explanations for reason codes).
- **TensorFlow** autoencoder or sequence model for behavioural anomaly signals (ATO, bot).
- **scikit-learn** for baselines, calibration, isolation forests.
- Models served as a lightweight in-cell service.
- **Feast** for online/offline feature consistency. **MLflow** for registry and lineage.

## Consequences

- **Positive:** latency, explainability (FR-FRD-05, Art. 22), training/serving skew control.
- **Negative / debt accepted:** ensemble complexity; feature store adds infrastructure.
- **Risks and mitigations:** deep models are an enhancement, not the foundation.

## Governance

Model cards, validation gates, champion/challenger rollout, drift monitoring (Phase 3 and 6).

## Revisit trigger

Feature-store ops cost exceeds benefit → compute features in the streaming job and cache in Redis.