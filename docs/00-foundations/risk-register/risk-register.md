# Project Risk Register (Phase 0 Seed)

Columns: ID, Risk, Likelihood, Impact, Treatment, Owner, Residual.

| ID | Risk | Likelihood | Impact | Treatment | Owner |
|---|---|---|---|---|---|
| PR-1 | Scope creep across four large domains | High | High | Fixed vertical slice; MoSCoW; defer list | Architect |
| PR-2 | Over-engineering (blockchain/ML for show) | Medium | High | Every tech needs an ADR with a "why not simpler" answer | Architect |
| PR-3 | Unsupported claims on regulations | Medium | High | Cite article/requirement numbers; verify against primary sources | Compliance |
| PR-4 | Live demo failure | Medium | High | Recorded backup; scripted, minimal-dependency demo | Architect |
| PR-5 | Decision criteria look biased to a favoured answer | Medium | Medium | Sensitivity analysis; document rejected options fairly | Architect |
| PR-6 | Presentation overruns 20 min | High | Medium | Timed rehearsals; hard cut line in slides | Architect |
| PR-7 | Assumptions invalid (regions, volumes) | Medium | Medium | Assumption register with revisit triggers | Architect |
| PR-8 | Real data accidentally used | Low | High | Synthetic-only policy; no real PAN/PII | DPO |
| PR-9 | Loss of work | Low | High | Git remote plus backup export | Architect |
| PR-10 | Knowledge gaps in a domain (e.g., customs) | Medium | Medium | Early study plan; glossary; "limits of my knowledge" framing | Architect |

## Notes

- This table grows into the Phase 1 risk register and the Phase 5 threat model.
- Add columns for **cause**, **rating**, and **residual risk** when the register matures.