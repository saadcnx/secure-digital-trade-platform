# Phase 3D: Payment Security & Digital Trade Infrastructure

**Roles:** Payments/Security Engineer (lead), Architect, DevSecOps
**Requirements:** FR-PAY-01 to FR-PAY-05, FR-PLT-01, NFR-02
**ADRs:** ADR-0002 (PCI scope), ADR-0006 (regional cells), ADR-0007 (schema classification)
**Risks:** R-01 (PAN exposure), R-09 (ATO at scale)

## 1. Tasks

### 1.1 Card capture

Browser loads PSP-hosted fields. PAN goes **browser → PSP only**. PSP returns a one-time payment token. Platform never sees PAN or CVV (FR-PAY-01).

### 1.2 Token abstraction

Payment Orchestrator maps PSP token → internal token ID (random, non-reversible, no PAN fragments beyond display data the PSP allows: last 4 + brand). All fraud features and logs use the internal token. **Mapping table is C2 — sensitive.**

### 1.3 Payment flow

Create order → fraud decision → if allow: authorise via PSP adapter; if step-up: trigger 3DS2 → capture after fulfilment rules → settle.

State machine per payment: `CREATED → AUTHORISED → CAPTURED → SETTLED / FAILED / REFUNDED`.

### 1.4 3DS/SCA

Fraud decision requests step-up, or a PSD2 exemption (e.g., low-risk transaction analysis) where risk is low. **Exemption use must stay within acquirer and regulatory limits — check current rules.**

### 1.5 Idempotency

Every payment call carries `Idempotency-Key`. Store key + request hash + result. Retry returns stored result. **Reused key with different body is rejected** (FR-PAY-05).

### 1.6 Multi-currency

Present in buyer's currency, settle in seller's or platform currency. Record FX rate, source, timestamp at transaction time. **Integer minor units (never floats) for money.**

### 1.7 Cross-border payment fraud

Risk signals: BIN country vs IP vs shipping country mismatch, high-risk corridors, rapid multi-currency switching. Feed into Risk Decision Service (Phase 3A).

### 1.8 API security

Gateway enforces OAuth2/OIDC, mTLS for partners, schema validation, rate limits per client, request signing for PSP webhooks (verify signature, check timestamp, reject replays).

### 1.9 Checkout page integrity

CSP, Subresource Integrity, inventory of every script with owner + justification (PCI Req. 6.4.3), tamper detection on payment page (Req. 11.6.1).

### 1.10 Reconciliation

Daily job matches PSP settlement reports to internal records, flags mismatches.

## 2. Decisions and Trade-offs

| Decision | Choice | Why | Trade-off |
|---|---|---|---|
| Capture method | Hosted fields (not full redirect) | Scope stays small with better UX | Page scripts stay in scope (Req. 6.4.3, 11.6.1); redirect would shrink scope further but costs conversion |
| Token design | Internal random token → PSP token | PSP portability, stable key for fraud features | Extra service to secure. Mapping table is sensitive (C2) |
| Consistency | Saga with outbox, not distributed transactions | PSP is external, two-phase commit impossible | Compensating actions (void/refund) must be designed |
| Capture timing | Auth at order, capture after screening release | Avoids refunding sanctioned or fraud orders | Auth hold expiry window limits how long a hold can last |
| Money handling | Integer minor units + ISO 4217 | No rounding errors | Needs conversion discipline in code |
| Webhooks | Signed, idempotent, replay-protected | PSP callbacks are an attack surface | Needs clock sync + nonce store |
| Multi-PSP | Adapter interface, one PSP in demo | Avoids lock-in | Differences in features leak through abstraction |

## 3. Diagram: Payment Component View (C4 L3)

See `docs/diagrams/3.4-payment-components.drawio`.

- **Left:** Browser with PSP iframe (red dashed "out of platform CDE") → PSP.
- **Centre:** Payment Orchestrator (State Machine, Token Mapper, PSP Adapter, 3DS Handler, FX Service, Idempotency Store, Reconciliation job).
- **Top:** Gateway → Checkout → Risk Decision → Orchestrator.
- **Right:** PSP/acquirer, 3DS ACS/issuer, FX rate source.
- **Bottom:** Kafka (`payment.authorised`, `payment.captured`) + restricted token DB (green dashed "connected system, in scope").
- **Stamp "No PAN"** on every internal arrow.
- **Sheet 2:** sequence — hosted fields → token → order → risk → (3DS) → authorise → screening release → capture.

## 4. Security, Privacy, and Controls

| Control | Requirement | Implementation |
|---|---|---|
| No PAN/CVV in logs, events, errors | PCI Req. 3 | DLP regex tests in CI |
| TLS 1.2+ externally, mTLS internally | PCI Req. 4 | Service mesh |
| MFA for admins | PCI Req. 8.4.2 | Keycloak (ADR-0014) |
| Scope review every 12 months | PCI Req. 12.5.2 | Scope diagram as living artifact |
| Token DB encrypted, access limited | PCI Req. 7 | KMS/HSM keys per cell, access logged |
| Webhook defence | PCI Req. 6 | Signature + timestamp tolerance + nonce |
| Card-testing defence | — | Per-IP/device/BIN velocity limits, CAPTCHA on risk, small-amount auth alerts |

Privacy: billing data is C2, in-region. FX + settlement analytics use aggregates.

**Note again:** tokenisation reduces scope, it doesn't remove it.

## 5. Failure Scenarios

| Scenario | Behaviour |
|---|---|
| PSP timeout after auth sent | Do not retry blindly. Query by idempotency key, then reconcile state |
| Duplicate request or webhook | Idempotency store returns original result |
| PSP down | Circuit breaker, queue non-urgent captures, clear retry message, optional second PSP |
| 3DS challenge abandoned | Order → `PENDING_PAYMENT` with expiry, then auto-cancel |
| Capture after late sanctions hit | Void the authorisation or refund, log compensating action |
| FX source unavailable | Last good rate within staleness limit, else block cross-currency presentment |
| Script injection on checkout page | CSP/SRI violation report, tamper alert, page rollback |

## 6. Examiner Questions

**Q: How do you prevent double charges when a PSP call times out?**
Strong: "Idempotency keys plus a payment state machine. On timeout I query the PSP by key rather than resending, and the reconciliation job catches the rest. Distributed transactions aren't possible with an external PSP, so I use a saga with compensating void or refund."
Weak: "We retry until it works."

**Q: Why authorise first and capture later?**
Strong: "It lets screening and async fraud checks finish before money moves, avoiding refunds for sanctioned or fraudulent orders. The limit is the authorisation validity window, so long holds need re-authorisation or a shorter review SLA."
Weak: "That's how PSPs work."

**Q: What PCI obligations remain with hosted fields?**
Strong: "Protecting the integrity of the payment page and scripts (Req. 6.4.3, 11.6.1), managing the PSP as a service provider, completing the correct SAQ, and ensuring no PAN leaks into logs or support tools. I would confirm SAQ type with the acquirer or QSA."
Weak: "None, the PSP handles it."