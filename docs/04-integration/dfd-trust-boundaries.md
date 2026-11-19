# Phase 4B: Data Flow Diagrams, Trust Boundaries & Resilience

**Roles:** Architect (lead), GRC/DPO (cross-border flows), DevSecOps (resilience tests), domain engineers (flow validation)
**Requirements:** PRV-01, FR-FRD-07, NFR-02, NFR-07
**ADRs:** ADR-0002 (PCI scope), ADR-0004 (fraud lawful basis), ADR-0007 (schema classification)
**Risks:** R-06 (cross-border transfer), R-08 (fraud-service outage)
**Milestone M4:** one order, order-to-delivery, traced across all domains, every trust boundary identified.

## 1. Tasks

### 1.1 DFD Level 0

Platform as a single process; only external entities:

- Buyer, Seller, Carrier, PSP, 3DS/issuer, list publishers (OFAC/EU/UN/UK/BIS), customs, analysts.

Every arrow carries a data class label.

### 1.2 DFD Level 1

Six processes:

1. Checkout/Order
2. Risk Decision
3. Payment
4. Compliance
5. Supply Chain
6. Privacy/Case

Data stores:

- Order DB, Token DB, Feature store, List store, Telemetry DB, Audit log, Ledger.

### 1.3 Trust boundaries (STRIDE applied at each in Phase 5)

| ID | Boundary |
|---|---|
| TB1 | Internet → Edge (WAF/Gateway) |
| TB2 | Edge → Service mesh |
| TB3 | Mesh → Restricted data tier (Token DB, C2 stores) |
| TB4 | Cell → Global control plane |
| TB5 | Cell → Cell (cross-border) |
| TB6 | Platform → External parties (PSP, carriers, list feeds) |
| TB7 | IoT device → MQTT broker |
| TB8 | Platform → Fabric consortium |

### 1.4 Cross-border flow register

Every flow leaving a cell: data, class, purpose, transfer basis (SCC/TIA or "non-personal"), owner.

Cross-border purchase: only minimum shipment data goes from buyer's cell to seller's cell.

| Flow | Data | Class | Purpose | Basis | Owner |
|---|---|---|---|---|---|
| Buyer cell → Seller cell | Ship-to name, address, order ref | C2 | Fulfilment | SCC + TIA | DPO |
| Cell → Global plane | Aggregates, hashed signals, policy/metrics | C0/C1 | Control + analytics | Non-personal | Architect |
| Cell → PSP | Token (no PAN) | C1 | Payment | Contract | Payments |

Register links to ROPA (GDPR Art. 30) and transfer register.

### 1.5 End-to-end trace (order-to-delivery)

1. Browser PAN → PSP (hosted fields), token returned.
2. Gateway → Checkout → Risk (100 ms) → decision.
3. Payment authorise (3DS if step-up).
4. `order.placed` from outbox to Kafka.
5. Compliance screening → `order.release` or `order.hold`.
6. After release: capture, fulfilment signal to seller.
7. Custody events to ledger; telemetry via MQTT; anomalies to Case Mgmt.
8. `DELIVERED` → settlement, reconciliation.

### 1.6 Resilience patterns per dependency

| Dependency | Pattern | Why | Trade-off |
|---|---|---|---|
| Checkout → Risk | Timeout 100 ms + circuit breaker + fallback rules | Protect revenue (ADR-0004) | Fallback is weaker |
| Checkout → PSP | Timeout, idempotency, circuit breaker, optional 2nd PSP | External system may be unreliable | Multi-PSP complexity |
| Order → Compliance | Async + hold gate (fail-closed) | Legal risk | Customer wait |
| Services → Kafka | Outbox + retry + DLQ | No event loss | Duplicates, dedup logic |
| Supply Chain → Fabric | Off-chain queue, async commit | Shipment doesn't stop on ledger outage | Ledger delayed |
| Cell → Global plane | Cache + last-known-good config | Control plane failure doesn't stop cells | Stale policy risk, freshness alarm |
| Bulkheads | Separate thread pools, namespaces, quotas per domain | One domain's overload doesn't take down others | Resource under-utilisation |
| Load shedding | Non-critical (analytics, review analysis) first | Protect checkout | Reporting delay |

**Sync vs async rule repeated:** if a failure there should not stop checkout, it is async. Only Risk and Payment are sync in the checkout path.

**Cross-border trade-off:** buyer-cell processing gives data minimisation, but the seller needs an address for delivery. So only ship-to details go to seller/carrier's cell, with documented transfer.

### 1.7 Graceful degradation matrix

| Component down | Checkout | Fulfilment | Notes |
|---|---|---|---|
| Risk scorer | Works (fallback tiers) | Works | Async re-score to catch leakage |
| Screening service | Works | Hold | Fail-closed |
| Kafka | Orders queued in DB outbox | Delayed | Replay on recovery |
| Fabric | Works | Works | Custody events queue |
| PSP | Down/degraded | n/a | 2nd PSP or retry message |
| MQTT broker | Works | Works | Visibility delayed, devices buffer |
| Control plane | Works | Works | Last-known-good policy |
| Redis | Works | Works | Stricter fallback tier |

### 1.8 Time budget (checkout path)

| Step | Budget |
|---|---|
| Gateway | 20 ms |
| Risk Decision | 100 ms |
| Payment authorise | PSP-dependent |

Only these are sync.

## 2. Failure Scenarios

| Scenario | Designed behaviour |
|---|---|
| Cascading failure (retry storm) | Exponential backoff + jitter, circuit breakers, retry budgets |
| Region/cell outage | Same-zone DR cell, failover runbook |
| Partial network partition | Idempotency + reconciliation jobs |
| Flash sale 10× | Autoscale, load shedding, queue-based levelling |

## 3. Diagrams (draw.io)

| Diagram | File |
|---|---|
| DFD Level 0 | `4.2-dfd-level0.drawio` |
| DFD Level 1 (one cell) | `4.3-dfd-level1.drawio` |
| Cross-border flow | `4.4-cross-border-flow.drawio` |
| Degradation matrix (heat table) | `4.5-degradation-matrix.drawio` |

Notes:
- DFD L0: platform circle centre, external entities around. Note: "Card data: browser → PSP only."
- DFD L1: six process circles, data stores as open rectangles, Kafka as a bar. TB1–TB8 as red dashed boxes with labels. Restricted tier (TB3) contains Token DB and C2 stores. Each flow labels data, class, sync/async.
- Cross-border: three cell boxes, only two arrow types — "C1 aggregates/hashed signals (allow-listed)" and "Minimal shipment data (SCC + TIA)". Globe icon on every arrow. Legend: "C2/C3 does not cross by any other path."
- Degradation: rows = components, columns = checkout/fulfilment/compliance/visibility. Green/amber/red. One slide = full resilience story.

## 4. Security, Privacy, and Controls

| Boundary | Control |
|---|---|
| TB1 | WAF + rate limit |
| TB2 | mTLS + OIDC |
| TB3 | Default-deny + MFA + per-service identity |
| TB4/TB5 | Signed artefacts + allow-list |
| TB6 | Adapter + signature verification |
| TB7 | Device certs + topic ACLs |
| TB8 | MSP roles |

- Cross-border register linked to ROPA + transfer register.
- Correlation ID in every flow; payload never in logs.
- DR pair in same residency zone (ADR-0008).

## 5. Examiner Questions

**Q: What is your single biggest failure-propagation risk?**
Strong: "Retry storms and synchronous dependency chains. So the checkout path has only two sync calls, each with timeout and circuit breaker, retry budgets, jitter. Everything else is async with bulkheads, so one domain's failure doesn't take down another."
Weak: "We don't have failures" or just "we retry."

**Q: How do you control cross-border data flow?**
Strong: "A flow register where every flow has data class and transfer basis. Structurally, C2 stays in its own cell, and only minimum shipment data transfers with SCC and TIA. CI policy check enforces the allow-list."
Weak: "We use a VPN."

**Q: Why are trust boundaries important in a DFD?**
Strong: "Threats happen where trust level changes. Every boundary gets STRIDE and a named control, so threat model and controls trace directly from the DFD."
Weak: "For the diagram."