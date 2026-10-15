# Simulated Elicitation — Interview Notes

5-line note per stakeholder: concern, constraint, objection, response, unresolved.

## Head of Payments

- **Concern:** Fraud losses and chargeback ratio.
- **Constraint:** Cannot raise decline rate to hit fraud target.
- **Objection:** Adaptive step-up hurts conversion.
- **Response:** Risk-tiered step-up; measure conversion lift via A/B.
- **Unresolved:** Auth-rate SLA with PSP.

## Growth/Product

- **Concern:** Checkout conversion; seller onboarding speed.
- **Constraint:** Cannot accept >100 ms added latency at checkout.
- **Objection:** Screening every order slows fulfilment.
- **Response:** Sync screening only on parties; async re-screen on list change.
- **Unresolved:** KYC effort for new sellers.

## CISO

- **Concern:** Breach risk, PCI scope, supply-chain risk of OSS.
- **Constraint:** No raw PAN anywhere outside PSP boundary.
- **Objection:** Fabric adds attack surface and skills burden.
- **Response:** Scope ledger to custody evidence; SBOM and signed images.
- **Unresolved:** HSM strategy for demo.

## DPO

- **Concern:** GDPR/CCPA lawfulness; cross-border transfers.
- **Constraint:** Personal data stays in region.
- **Objection:** Fraud team wants rich features; minimisation says fewer.
- **Response:** Pseudonymised features, purpose-limited retention, per-attribute necessity review.
- **Unresolved:** Retention period for fraud features (to be justified in DPIA).

## Trade Compliance Officer

- **Concern:** Sanctions, HS classification accuracy, customs penalties.
- **Constraint:** 100% of orders screened pre-fulfilment.
- **Objection:** Fuzzy-match false positives delay legit orders.
- **Response:** Tiered thresholds, whitelist with expiry, fast review SLA.
- **Unresolved:** Ownership data for 50 Percent Rule.

## Engineering/SRE

- **Concern:** Operability of Fabric + ML pipelines.
- **Constraint:** Small team; on-call load.
- **Objection:** Too many moving parts to run reliably.
- **Response:** Vertical slice; managed-style MLOps; degrade paths.
- **Unresolved:** Model retraining cadence.