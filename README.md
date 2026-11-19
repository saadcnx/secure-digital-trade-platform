# Phase 5: Security, Privacy & Governance

**Effort:** 1.5–2 weeks | **Primary roles:** architect, Payments/Security Engineer, GRC/DPO, DevSecOps

**Output:** STRIDE threat model per TB1–TB8, abuse cases, PCI control mapping, identity/crypto design, DPIA, lawful basis register, ROPA, DSAR orchestration, retention schedule, LINDDUN-lite, governance RACI, IR plan.

## Contents

- `threat-model-identity-crypto.md` — Phase 5A: threat modelling, identity, cryptography, PCI controls
- `privacy-dpia-governance.md` — Phase 5B: DPIA, residency, DSAR, retention, governance, IR

## Diagram files (draw.io, in `docs/diagrams/`)

| Diagram | File |
|---|---|
| 5.1 Security Architecture | `5.1-security-architecture.drawio` |
| 5.2 Data Residency Map | `5.2-data-residency.drawio` |
| 5.3 DSAR Sequence | `5.3-dsar-sequence.drawio` |
| 5.4 Privacy Lifecycle | `5.4-privacy-lifecycle.drawio` |
| 5.5 RACI + IR Timeline | `5.5-raci-ir-timeline.drawio` |

## Cross-references

- Phase 4 trust boundaries: `docs/04-integration/dfd-trust-boundaries.md`
- ADRs: `docs/adr/`
- DPIA screening (Phase 1): `docs/01-requirements/dpia-screening/dpia-screening.md`
- PCI scope (Phase 1): `docs/01-requirements/pci-scope/pci-scope.md`

## Exit criteria (Milestone M5)

- ☐ Threat model reviewed; TB1–TB8 each have STRIDE + control + residual
- ☐ Abuse cases documented
- ☐ PCI control mapping verified against primary source
- ☐ Identity design: users, partners, admins, workloads
- ☐ Crypto design: envelope encryption, field-level, signing, secrets
- ☐ DPIA complete; residual risks signed by named role
- ☐ Lawful basis register, ROPA, processor register
- ☐ DSAR flow operational; retention schedule live
- ☐ LINDDUN-lite pass complete
- ☐ RACI approved; IR plan exercised via tabletop
- ☐ Baseline tagged `security-baseline-v1`