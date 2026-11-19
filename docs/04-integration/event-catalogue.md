# Phase 4A: Event Backbone, APIs & Integration Contracts

**Roles:** Architect (lead), DevSecOps, Payments/Security Engineer, all domain engineers for their contracts
**Requirements:** FR-PLT-01, PRV-01, PRV-04, NFR-02, NFR-05, NFR-07
**ADRs:** ADR-0002 (PCI scope), ADR-0003 (outbox/events), ADR-0007 (schema classification)
**Risks:** R-01 (PAN exposure), R-06 (cross-border transfer), R-08 (fraud-service outage)

## 1. Tasks

### 1.1 Event catalogue

| Event | Producer | Consumers | Class | Key |
|---|---|---|---|---|
| `order.placed` | Checkout | Compliance, Risk (async), Supply Chain | C2 refs | order_id |
| `risk.decided` | Risk Decision | Checkout, Case Mgmt, Analytics | C1 | order_id |
| `payment.authorised` | Payment Orchestrator | Checkout, Compliance, Reconciliation | C1 | order_id |
| `payment.captured` | Payment Orchestrator | Checkout, Compliance, Reconciliation | C1 | order_id |
| `payment.voided` | Payment Orchestrator | Checkout, Compliance, Reconciliation | C1 | order_id |
| `order.hold` | Compliance | Checkout, Payment, Notification | C1 | order_id |
| `order.release` | Compliance | Checkout, Payment, Notification | C1 | order_id |
| `custody.recorded` | Supply Chain | Order, Notification, Analytics | C1 (hashed refs) | shipment_id |
| `telemetry.anomaly` | Stream processor | Case Mgmt, Supply Chain | C1 | shipment_id |
| `case.resolved` | Case Mgmt | Risk, Compliance (labels) | C2 restricted | case_id |
| `dsar.requested` | Privacy | All services holding personal data | C2 refs | subject_id |
| `dsar.completed` | Privacy | All services holding personal data | C2 refs | subject_id |

### 1.2 Event envelope (every event)

```json
{
  "event_id": "uuid",
  "type": "order.placed",
  "schema_version": 3,
  "occurred_at": "ISO-8601",
  "cell_id": "eu-1",
  "correlation_id": "gateway-generated-uuid",
  "data_class": "C2",
  "producer": "checkout-service",
  "payload": {}
}
```

`correlation_id` is propagated from the gateway so one order can be traced across all domains.

### 1.3 Topic design

Pattern: `{cell}.{domain}.{event}.v{n}`

- Key by `order_id` (or `shipment_id`) to keep per-order ordering.
- Replication factor 3, min ISR 2.
- Retention per class: C2 topics short (72 h), audit topics long (≥ 12 months, PCI Req. 10.5.1).

### 1.4 Sync vs async rules

**Sync only if the caller cannot proceed without the answer:**

- Gateway → Checkout
- Checkout → Risk (100 ms deadline)
- Checkout → Payment

Everything else is async. Rule of thumb: if a failure there should not stop checkout, it is async.

### 1.5 Reliability patterns

| Pattern | Implementation |
|---|---|
| Transactional outbox | Debezium or polling relay — DB write and event publish atomic |
| Idempotent consumers | Processed-event table per consumer |
| Dead-letter topics | Per consumer, with alerting |
| Retry | Exponential backoff with max, then DLQ |

### 1.6 Schema governance

- Avro or Protobuf in Schema Registry, **BACKWARD compatibility**.
- CI fails on a breaking change or a missing `data_class` tag.
- Consumer-driven contract tests (Pact) for REST and gRPC.

### 1.7 API design

- External: REST with OpenAPI 3. Versioning in URL path.
- Internal: gRPC.
- Standard error model, pagination, `Idempotency-Key` on all unsafe operations.

### 1.8 API gateway policy (APISIX or Kong)

- OIDC token validation
- Scopes per route
- Rate limits per client and per IP
- Request size caps
- Schema validation
- WAF rules
- Bot-defence hook
- mTLS for partners

### 1.9 Mesh policy (Istio)

Default-deny `AuthorizationPolicy`. Allow only listed service identities and methods. Example: only `payment-orchestrator` may call `token-mapper`.

### 1.10 External integrations

PSP, 3DS, carriers, sanctions feeds, customs interfaces. Each through an adapter with its own timeout, circuit breaker, and contract tests with a stub. Webhooks signed, idempotent, replay-protected.

### 1.11 Cross-cell replication

MirrorMaker 2 with an allow-list of **C0/C1 topics only**. CI policy check rejects any allow-list change that includes a C2-tagged schema.

## 2. Decisions and Trade-offs

| Decision | Choice | Why | Trade-off |
|---|---|---|---|
| Event style | Thin events (IDs + refs), fetch-on-need for C2 | Keeps personal data off shared topics (Art. 25) | Extra lookup calls, tighter coupling to source service |
| Consistency | Outbox + eventual consistency | No distributed transactions across services | Consumers tolerate delay and duplicates |
| Delivery semantics | At-least-once + idempotent consumers | Simpler and more robust than exactly-once end to end | Dedup logic in every consumer |
| Serialisation | Avro/Protobuf with registry | Compact, enforced contracts | Tooling overhead vs plain JSON |
| Internal protocol | gRPC internally, REST externally | Speed and typing inside, familiarity outside | Two styles to maintain |
| Orchestration vs choreography | Choreography for main flow, orchestration (state machine) only in payments | Low coupling in most places, payments need explicit compensation | Choreography harder to see end to end — rely on correlation IDs and tracing |
| Gateway | APISIX or Kong (open source) | Plugins for auth, rate limit, WAF hooks | Plugin/config sprawl — keep in GitOps |

## 3. Diagram: Event Flow Diagram

See `docs/diagrams/4.1-event-flow.drawio`.

- **Centre:** wide Kafka bar with topic labels. Services above and below.
- **Producers (top)** write via outbox icons into the bar.
- **Consumers (bottom)** read from it.
- Colour events by class: **C1 green, C2-ref amber. No red (no C3) on the bar — state in legend.**
- **Right edge:** MirrorMaker allow-list arrow to global plane, labelled "C0/C1 only".
- **DLQ box under each consumer.**
- **Sheet 2:** order-to-delivery sequence with `correlation_id` on every message.

## 4. Security, Privacy, and Controls

- Gateway is the only public entry. Mesh policy default-deny; every call carries a verified identity.
- No C2 on shared topics unless field-level encrypted. Prefer references.
- Schemas without `data_class` tag fail the build.
- Topic ACLs follow least privilege (a service can write only its own topics).
- Webhooks: signature, timestamp tolerance, nonce.
- Logs carry `correlation_id`, never payloads containing personal data.
- Rate limits at edge support fraud-fallback defence (attackers cannot easily force load).

## 5. Failure Scenarios

| Scenario | Behaviour |
|---|---|
| Consumer crashes mid-processing | Resumes from offset, idempotency table prevents double effects |
| Poison message | Retries, then DLQ with alert and replay tool after fix |
| Schema break shipped | CI blocks it. If one slips through, registry rejects incompatible producers |
| Kafka lag grows | Autoscale consumers, lag alert, non-critical consumers shed load first |
| Outbox relay stops | Rows accumulate safely in DB, alert on outbox age |
| Duplicate or out-of-order events | Per-key ordering, version/sequence checks, idempotent handlers |
| Gateway overload | Rate limiting, priority for checkout routes, autoscale |

## 6. Examiner Questions

**Q: How do you guarantee an event is published when the order is saved?**
Strong: "The transactional outbox. The order and the event are written in one local transaction, and a relay publishes it. This avoids dual-write inconsistency without distributed transactions. Delivery is at-least-once, so consumers are idempotent."
Weak: "We publish right after saving."

**Q: Choreography or orchestration? Why?**
Strong: "Choreography for most flows to keep coupling low. Orchestration only in payments, where compensation like void or refund must be explicit. The cost of choreography is poor visibility, so I rely on correlation IDs and distributed tracing."
Weak: "Choreography is better."

**Q: How do you stop a schema change from breaking consumers?**
Strong: "Schema registry with backward compatibility checks in CI, consumer-driven contract tests, and versioned topics for real breaking changes with a deprecation window. Missing classification tags also fail the build."
Weak: "We tell the other teams."