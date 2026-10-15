# ADR-0013: Compliance as policy-as-code — OPA plus a dedicated screening service

- **Status:** Accepted
- **Date / Owner:** Phase 2 / Compliance Engineer

## Context

FR-CMP-05, BD-4, NFR-03/04, R-03.

## Decision

Jurisdiction rules (document requirements, restricted goods, thresholds) expressed in **Open Policy Agent (Rego)**, versioned in Git, distributed as signed bundles, with tests. A **screening service** handles list ingestion, normalisation, fuzzy matching, and case creation.

## Data sources

Prefer official lists (OFAC SDN/Consolidated, EU, UN, UK) ingested directly. Aggregators such as OpenSanctions have licence terms that may restrict commercial use (verify).

## Fail-closed rule

Sanctions is **fail-closed for fulfilment**: if screening is unavailable, the order is accepted but **held**, never shipped unscreened.

## Consequences

- **Positive:** agility, auditability, testability.
- **Negative / debt accepted:** Rego skill requirement; policy sprawl risk; fuzzy-match tuning is ongoing.

## Revisit trigger

Screening false-positive review load exceeds analyst capacity → reconsider commercial screening data or ML-assisted matching.