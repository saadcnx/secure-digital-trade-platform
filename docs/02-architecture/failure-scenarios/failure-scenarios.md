# Failure Scenarios and Recovery (Phase 2)

| Scenario | Impact | Designed behaviour | Recovery |
|---|---|---|---|
| **Risk scorer down or slow** | Checkout latency or block | Timeout at 100 ms; circuit breaker opens; fallback rules by risk tier | Auto-restart; replay events for async re-scoring; alert if fallback exceeds threshold |
| **Attackers induce fallback** (deliberate load) | Weaker fraud controls | Rate limits + bot defence at the edge; fallback stricter for high-risk signals | Block sources; scale scorer; review fallback losses |
| **Kafka broker / partition failure** | Delayed async flows | RF=3, min ISR=2; outbox retains events | Failover; consumers resume from offsets |
| **Screening service down** | Orders unscreened | **Fail-closed for fulfilment:** orders held, customers informed | Restore; process backlog; SLA on hold time |
| **Stale sanctions list** | Missed hit | Freshness alert at 1 h threshold; last-updated shown in decisions | Manual ingest; batch re-screen after refresh |
| **Fabric peer / orderer outage** | Custody events delayed | Queue events off-chain; commit when restored; Raft tolerates minority loss | Peer resync; reconcile queue |
| **Cell outage** | Region unavailable | Redirect to DR cell within the same residency zone | Failover runbook; RPO ≈ 0 for Tier 0 via in-zone replication |
| **Bad policy bundle published** | Mass wrongful holds or misses | Signed, staged rollout; automated policy tests; instant rollback | Revert Git commit; Argo CD resync |
| **Poisoned or drifted model** | Fraud leakage or false positives | Champion/challenger; validation gates; drift alerts; one-click rollback | Revert to prior model; investigate data |
| **Control plane compromise** | Wrong policies/models pushed everywhere | Signing keys offline or HSM-held; cells verify signatures; control plane holds no C2 | Rotate keys; cells keep last-known-good config |

## Single-point-of-risk answer

The control plane is the one shared component. It was designed to hold no personal data and to be unable to push unsigned artefacts.