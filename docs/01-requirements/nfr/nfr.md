# Non-Functional Requirements (with numbers)

All numbers are **assumptions** — register them. Base: 500 orders/sec peak (10× flash-sale headroom), 50,000 IoT devices reporting every 30 s (~1,700 msg/s).

| ID | Quality attribute | Target | Measurement / verified in |
|---|---|---|---|
| NFR-01 | Fraud scoring latency | p99 < 150 ms (service); p50 < 50 ms | k6 load test, Phase 7 |
| NFR-02 | Checkout-path availability | 99.95% monthly (~22 min) | SLO dashboard, Phase 6-7 |
| NFR-03 | Sanctions screening latency | p95 < 500 ms per party (sync); batch re-screen within 4 h of list change | Test, Phase 7 |
| NFR-04 | List freshness | New entries active in ≤ 1 h after publication | Pipeline test |
| NFR-05 | Ledger commit latency | p95 < 3 s per custody event | Hyperledger Caliper |
| NFR-06 | IoT alerting | Breach alert raised ≤ 60 s from message receipt | End-to-end timer |
| NFR-07 | Scalability | Sustain 10× peak order rate with horizontal scaling, no redesign | Load test |
| NFR-08 | Audit log retention | ≥ 12 months, last 3 months immediately available (PCI DSS Req. 10.5.1) | Config review |
| NFR-09 | Data subject requests | Fulfil within 1 month (GDPR Art. 12(3)); CCPA within 45 days | Workflow test |
| NFR-10 | Breach notification readiness | Supervisory authority notice within 72 h of awareness (GDPR Art. 33) | IR tabletop |
| NFR-11 | Fraud model quality | Recall ≥ 85% at FPR ≤ 0.5% | Synthetic data eval (caveat) |
| NFR-12 | Explainability | Reason codes on 100% of non-allow decisions | Automated check |

## Honesty point

NFR-11 uses **synthetic data** — real-world performance will differ. Say so. Inflated metrics are punished harder than modest honest ones.

## BIA tiers (RPO/RTO)

| Tier | Services | RPO | RTO | Rationale |
|---|---|---|---|---|
| 0 | Checkout, payment token service, fraud scorer | ~0 (sync replication in region) | 15 min | Direct revenue and card-acceptance impact |
| 1 | Sanctions screening, custody ledger, API gateway | ≤ 5 min | 30-60 min | Legal exposure and shipment holds |
| 2 | IoT ingestion, analytics, model training | ≤ 1 h | 4 h | Degradable without immediate loss |
| 3 | Reporting, dashboards | 24 h | 24 h | Not time-critical |