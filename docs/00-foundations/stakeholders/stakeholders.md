# Stakeholder Map

| Stakeholder | Top concern | Veto power | Likely conflict |
|---|---|---|---|
| Head of Payments/Finance | Fraud losses, chargeback rate, auth rates | Budget | Wants aggressive blocking; Growth wants fewer declines |
| Growth/Product | Checkout conversion, seller onboarding speed | Roadmap | Friction from step-up auth and screening |
| CISO | Breach risk, PCI scope | Release gate | Wants controls that slow delivery |
| Data Protection Officer | GDPR/CCPA lawfulness, data transfers | Processing approval | Wants minimisation; Fraud team wants rich data |
| Trade Compliance Officer | Sanctions, customs accuracy | Shipment holds | False positives delay legitimate orders |
| Logistics partners / carriers | Simple integration | Adoption | IoT and ledger onboarding burden |
| Sellers / buyers | Fairness, speed, privacy | Churn | Wrongful blocks, unexplained decisions |
| Regulators / auditors | Evidence and accountability | Licence | Demand explainability and records |
| Engineering / SRE | Operability, on-call load | Practical | Complexity of Fabric and ML ops |

## Key conflicts to name in the presentation

- **Fraud analytics vs data minimisation** → pseudonymised features, purpose-limited retention, regional cells.
- **Conversion vs security friction** → adaptive step-up; only risk-proportionate challenges.
- **Immutability vs right to erasure** → PII off-chain; only hashes on-chain.