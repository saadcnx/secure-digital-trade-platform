# Phase 4: Event Backbone, APIs & Integration

**Effort:** 1–1.5 weeks | **Primary roles:** architect, DevSecOps, domain engineers

**Output:** event catalogue, integration contracts, DFDs L0/L1, trust boundaries TB1–TB8, cross-border flow register, resilience matrix, examiner Q&A.

## Contents

- `event-catalogue.md` — Phase 4A: events, envelope, topics, reliability, APIs, gateway/mesh policy, examiner Q&A
- `dfd-trust-boundaries.md` — Phase 4B: DFDs, trust boundaries, cross-border register, resilience, degradation matrix, examiner Q&A

## Diagram files (draw.io, in `docs/diagrams/`)

| Diagram | File |
|---|---|
| 4.1 Event Flow | `4.1-event-flow.drawio` |
| 4.2 DFD Level 0 | `4.2-dfd-level0.drawio` |
| 4.3 DFD Level 1 (one cell) | `4.3-dfd-level1.drawio` |
| 4.4 Cross-border flow | `4.4-cross-border-flow.drawio` |
| 4.5 Degradation matrix | `4.5-degradation-matrix.drawio` |

## Cross-references

- Phase 3 design: `docs/03-design/`
- ADRs: `docs/adr/`
- Requirements: `docs/01-requirements/rtm/rtm.md`
- NFRs: `docs/01-requirements/nfr/nfr.md`

## Exit criteria (Milestone M4)

- ☐ One order traced end-to-end with `correlation_id` across all domains
- ☐ All 8 trust boundaries identified and mapped to controls
- ☐ Cross-border flow register complete, linked to ROPA
- ☐ Degradation matrix reviewed by simulated stakeholders
- ☐ Event catalogue complete; every event has a schema and class
- ☐ CI gates in place for schema compat and `data_class` tag
- ☐ Baseline tagged `integration-baseline-v1`