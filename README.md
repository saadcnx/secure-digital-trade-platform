# Phase 2: High-Level Architecture & Strategic Decisions

**Effort:** 1–1.5 weeks | **Primary roles:** you, plus input from all engineers
**Output:** frozen architecture baseline, C4 L1/L2 plus deployment diagrams, ADRs 0005–0015.

## Contents

- `asr/` — Architecturally significant requirements
- `matrix/` — Platform-style decision matrix with sensitivity check
- `capability-map/` — Capability map (build/adopt/buy colouring)
- `build-adopt-buy/` — Technology selection table
- `integration-points/` — Phase 2 level integration and data flow
- `security-controls/` — Phase 2 controls mapped to ADRs
- `failure-scenarios/` — Designed degraded behaviour
- `best-practices/` — Industry practices reflected
- `examiner-qa/` — Ten examiner Q&A
- `demo-ideas/` — Practical demos
- `roles/` — Role simulation
- `exit-checklist/` — Milestone M2
- `diagrams/` — Diagram specs (draw.io)
- `../adr/0005..0015` — The architecture decisions

## Correction carried from Phase 0

Platform-style matrix arithmetic: modular monolith **365**, event-driven microservices **390**, serverless **345**. Ranking unchanged; recompute any matrix yourself.