# Phase 1 Initial Risk Assessment — Top 10

Scoring: likelihood (1-5) × impact (1-5). Rating: 1-6 low, 8-12 medium, 15-25 high.

| ID | Risk | L | I | Score | Treatment | Links to phase |
|---|---|---|---|---|---|---|
| R-01 | PAN exposure through logs, events, or errors | 3 | 5 | 15 | Scope reduction; log scrubbing; DLP tests | P3, P5 |
| R-02 | Sanctioned-party transaction fulfilled (false negative) | 2 | 5 | 10 | Multi-list screening; ownership checks; batch re-screen | P3 |
| R-03 | Stale sanctions or rules data | 3 | 4 | 12 | Freshness SLO and alerting | P3, P6 |
| R-04 | Fraud model drift or poisoning | 3 | 4 | 12 | Monitoring, drift alerts, validation gates | P3, P6 |
| R-05 | Excessive false positives harm conversion and fairness | 4 | 3 | 12 | Cost-weighted thresholds; bias tests; appeal | P3 |
| R-06 | Unlawful cross-border transfer | 2 | 5 | 10 | Regional cells; transfer register; TIA | P2, P5 |
| R-07 | IoT spoofing or sensor tampering | 3 | 3 | 9 | Device identity and attestation; plausibility checks | P3, P5 |
| R-08 | Fraud-service outage blocks checkout | 3 | 4 | 12 | Fallback rules; circuit breaker | P4, P7 |
| R-09 | Account takeover at scale (credential stuffing) | 4 | 4 | 16 | Bot defence; MFA; breached-password checks | P3 |
| R-10 | Ledger or ML complexity exceeds team capacity | 3 | 3 | 9 | Scope ledger to custody evidence; managed-style MLOps | P2 |

## Treatment strategies

Each treatment names strategy (**reduce / avoid / transfer / accept**) and a residual-risk owner.