# Integration Points and Data Flow (Phase 2 Level)

| From | To | Mode | Data class | Notes |
|---|---|---|---|---|
| Browser | PSP | Sync (hosted fields) | C3 (PAN) | Never touches platform |
| Gateway | Checkout | Sync REST | C2 | OIDC token, rate-limited |
| Checkout | Risk Decision | Sync gRPC, 100 ms deadline | C2 pseudonymised | Circuit breaker |
| Checkout / Risk | Payment Orchestrator | Sync | Token only | Idempotency key |
| Checkout | Kafka | Async via outbox | C1/C2 refs | `order.placed` |
| Kafka | Compliance | Async | C2 refs | Screening → hold/release events |
| IoT devices | MQTT → Kafka | Async | C1 | Device cert auth |
| Supply Chain | Fabric | Sync/async | Hashes only | Ledger-gateway abstraction |
| Cell | Global plane | Async, filtered | C0/C1 only | Policy-checked replication |
| Case Management | Risk/Compliance | Async | C2 (restricted) | Human decisions feed back as labels |