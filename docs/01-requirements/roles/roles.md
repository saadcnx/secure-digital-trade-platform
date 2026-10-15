# Roles in Phase 2 and How to Simulate Them

| Role | Work in this phase | Exam simulation |
|---|---|---|
| **You (Architect)** | Own all ADRs, matrices, diagrams | Present the decision map and defend 3 ADRs |
| **ML/Fraud Engineer** | Validates latency budget, feature store choice, fallback design | "The ML engineer confirmed XGBoost inference at ~X ms in our test, so the budget holds" (use your own measurement) |
| **Compliance/Trade Engineer** | Validates fail-closed hold design and OPA approach | Quote a rule-change example going through Git |
| **Blockchain/IoT Engineer** | Challenges ledger scope, proposes abstraction | "The engineer wanted more on-chain; I limited it for privacy and performance" |
| **Payments/Security Engineer** | Reviews token abstraction and mesh policy | Present the PCI scope effect of ADR-0002 |
| **DevSecOps Engineer** | Validates GitOps, cell reproducibility, fitness functions | Show cell creation as code |
| **GRC/DPO** | Reviews cell design and transfer rules | "DPO approved cells on condition that the control plane holds no C2" |