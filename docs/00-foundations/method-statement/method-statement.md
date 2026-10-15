# Method Statement

Frameworks chosen for structure, threats, and decision records. Each choice is defended by fit for purpose and audience.

| Concern | Choice | Why | Alternatives considered | Trade-off |
|---|---|---|---|---|
| Describing structure | **C4 model** | Four zoom levels matching audience; tool-neutral; easy in draw.io | UML, ArchiMate, TOGAF artifacts | Less formal than ArchiMate; mitigate with a one-page capability map |
| Threat modelling | **STRIDE per DFD element + abuse cases** | Systematic; maps to DFD trust boundaries | PASTA, LINDDUN, attack trees | STRIDE under-covers privacy; add LINDDUN-lite pass in Phase 5 |
| Recording decisions | **ADRs** | Lightweight, versioned, auditable | Long design doc only | Needs discipline to keep current |
| Control language | **NIST CSF / SP 800-53 vocabulary**, mapped to PCI DSS and GDPR | Common language across regimes | ISO 27001 Annex A | NIST is US-centric; note ISO 27001 equivalence |

## Notes

- Record a practice ADR in `docs/adr/0001-frameworks-and-methods.md` to prove the template works.