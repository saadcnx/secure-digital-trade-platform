# Requirements Traceability Matrix (Sample Rows)

| BD | Req ID | Source / Regulation | Design element (planned) | Control (planned) | Test (planned) |
|---|---|---|---|---|---|
| BD-3 | FR-PAY-01 | PCI DSS Req. 3, 4 | Hosted fields + token service (ADR-0002) | Scope boundary; CSP | Network capture shows no PAN to platform |
| BD-1 | FR-FRD-01 / NFR-01 | n/a | Real-time scorer + feature store | Latency SLO | k6 p99 < 150 ms |
| BD-2 | FR-CMP-01 | OFAC, EU lists | Screening service | List freshness; audit log | Seeded SDN-like test party blocked |
| BD-6 | PRV-04 | GDPR Art. 5(1)(c), 17, 25 | Off-chain PII, on-chain hash | Salted hashing | Erasure test: delete off-chain, hash unlinkable |
| BD-6 | PRV-03 | GDPR Art. 22 | Review and appeal workflow | Human-in-the-loop | Walk through an appeal case |
| BD-1 | FR-FRD-07 | n/a | Fallback rules and circuit breaker | Resilience pattern | Kill scorer; checkout continues in tiers |
| BD-4 | FR-CMP-05 | WCO, national rules | Policy-as-code repository | Versioned rules with tests | Add a new country rule via pipeline only |

## Exit rule

Every **Must** requirement has at least: a source, a planned design element, and a planned test. Columns fill progressively through Phase 2–4; verified status is completed in Phase 7.

## Traceability chain

```
BD → Req → Regulation → Design element → Control → Test → Exam answer
```

If you can walk any examiner question along this chain, you are operating at Level 6.