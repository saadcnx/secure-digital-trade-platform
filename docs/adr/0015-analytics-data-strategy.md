# ADR-0015: Analytics and data strategy — regional processing, global aggregates only

- **Status:** Accepted
- **Date / Owner:** Phase 2 / Architect + DPO

## Decision

Training and feature computation run **inside each cell**. The global plane receives only model **artefacts** and aggregate metrics. Shared fraud intelligence uses hashed, salted identifiers under a documented transfer basis. Federated learning is deferred.

## Why

Resolves conflict C5 structurally; gives a defensible privacy-by-design story (Art. 25).

## Consequences

- **Positive:** residency by construction; clean data-flow story for the DPIA.
- **Negative / debt accepted:** each region trains on less data; cold-start problem in new cells.

## Mitigation

Start from a global baseline model trained on synthetic or consented data, then fine-tune regionally.

## Revisit trigger

Regional model quality falls below NFR-11 targets → evaluate federated learning or privacy-enhanced aggregation.