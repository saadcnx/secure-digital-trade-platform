# Problem Statement

> Global marketplaces lose revenue and trust to payment fraud, account takeover, counterfeit goods, and non-compliant shipments, while simultaneously facing tightening obligations under PCI DSS, GDPR/CCPA, sanctions regimes, and customs rules. These risks are currently managed by siloed tools that each hold their own copy of customer and transaction data, which creates inconsistent decisions, large compliance scope, and no end-to-end visibility from order to delivery. The organisation needs a unified, cloud-native, open-source-based platform that makes fast, explainable, risk-proportionate decisions across fraud, compliance, supply chain, and payments, without violating data residency or privacy obligations.

## Who is harmed today

- Buyers (fraud, counterfeit goods, unexplained blocks)
- Sellers (chargebacks, delays, opaque decisions)
- Platform operator (chargebacks, fines, reputational risk)
- Regulators / customs (unreported shipments, sanctions evasion)

## Why now

- Regulatory tightening (PCI DSS v4.0.1, GDPR, CPRA, sanctions regimes)
- Cross-border growth ambition requires market entry in new jurisdictions
- Fragmented point solutions are inflating compliance scope and cost

## Constraints

- Cloud-agnostic on Kubernetes
- Open-source / cloud-native tooling
- No real PII or PAN in the demo (synthetic data only)