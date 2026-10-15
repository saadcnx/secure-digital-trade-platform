# Architecturally Significant Requirements (ASRs)

Extracted from the Phase 1 RTM. These ~10 requirements most constrain the structure.

| ASR | Source | Structural consequence |
|---|---|---|
| Fraud score p99 < 150 ms in checkout | NFR-01 | Co-located scorer, in-memory online features, hard timeout and fallback |
| 99.95% checkout availability | NFR-02 | No hard dependency on slow or optional services in the checkout path |
| Personal data stays in-region | PRV-01, REG | Regional cell architecture |
| No raw PAN on platform | FR-PAY-01/02 | PSP-hosted fields plus token abstraction |
| Screening before fulfilment, auditable | FR-CMP-01/06 | Hold-before-fulfilment gate; immutable decision log |
| Multi-party custody evidence | FR-SCV-01 | Shared ledger across organisations |
| PII off ledger | PRV-04 | Off-chain store plus on-chain hashes |
| Rules change without redeploy | FR-CMP-05 | Policy-as-code engine |
| 10× burst headroom | NFR-07 | Horizontal scale, async backbone |
| Human review of significant decisions | PRV-03 | Case management service |