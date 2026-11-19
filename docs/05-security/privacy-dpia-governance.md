# Phase 5B: Privacy, DPIA, Data Residency, Governance & Incident Response

**Roles:** GRC/DPO (lead), Architect, ML Engineer (bias/explainability), DevSecOps (retention, DSAR automation)
**Requirements:** PRV-01 to PRV-04, NFR-08, NFR-09, NFR-10, NFR-12
**Regulations:** GDPR Art. 5, 6, 12-22, 25, 28, 30, 32-35, 44-49; CCPA/CPRA
**Risks:** R-05 (false positives, fairness), R-06 (cross-border transfer)
**Milestone M5:** threat model reviewed, DPIA complete, residual risks accepted.

**Accuracy flag:** article numbers and CCPA thresholds are from memory. Verify against primary source (EUR-Lex, California AG). This is not legal advice; DPO and counsel finalise.

## 1. Tasks

### 1.1 Complete the DPIA (Art. 35)

Began in Phase 1 screening.

- **Processing description:** purposes, data categories, recipients, retention, transfers.
- **Necessity and proportionality:** per-attribute "why we need this" (feature-necessity review).
- **Risks to individuals:** wrongful block, profiling, location tracking, data breach, function creep.
- **Mitigations and residual risk.** If high residual remains, mention Art. 36 prior consultation.

### 1.2 Lawful basis register (Phase 1 Decision 3)

| Purpose | Basis |
|---|---|
| Fraud scoring | Legitimate interests (with LIA) |
| Sanctions screening | Legal obligation |
| Payment execution | Contract |
| Marketing | Consent (separate) |

### 1.3 ROPA (Art. 30) and processor register (Art. 28)

DPAs with PSP, carriers, cloud, SIEM vendors.

### 1.4 Data residency design

- User in one home cell.
- Per-cell keys.
- DR only in same zone.
- Cross-border flow register (Phase 4B) linked.

### 1.5 International transfers

Where needed: SCCs + Transfer Impact Assessment (Art. 44-49). Cross-border purchase: only minimum shipment data. Transfer register maintained.

### 1.6 DSAR orchestration (Privacy Service)

Request intake → identity verification → fan-out event `dsar.requested` → each service extracts or deletes its data → `dsar.completed` → consolidated response.

Deadlines: GDPR one month (Art. 12(3), extension possible); CCPA 45 days (verify). Backups: rolling expiry policy + re-apply deletion after restore.

### 1.7 Retention automation

Per-class TTL jobs:

| Class | Retention | Justification |
|---|---|---|
| Fraud features | 12–24 months | Justify per attribute in DPIA |
| Audit records | Legal minimum (≥ 12 months, PCI Req. 10.5.1) | Compliance |
| C2 personal | Purpose-timed | Minimisation |

Retention schedule linked to DPIA.

### 1.8 Erasure with ledger

Delete off-chain data and salt; on-chain only salted hash (ADR-0009). Note the legal debate that hashes may be personal data — minimise accordingly.

### 1.9 Privacy-preserving analytics

- Pseudonymisation (per-purpose HMAC keys).
- Aggregation with small-cell suppression.
- Differential privacy for published statistics (option).
- Federated learning deferred (future work).

### 1.10 Art. 22 / fairness

- Human review and appeal workflow.
- Reason codes.
- Bias testing by segment (false-positive rate parity).
- Quarterly model fairness report.
- EU AI Act classification assessment noted (check current Annex III).

### 1.11 CCPA/CPRA handling

- "Do Not Sell/Share" signal (Global Privacy Control) honoured.
- Sensitive PI limitation.
- Fraud/security exemptions documented.

### 1.12 LINDDUN-lite pass

Linkability, identifiability, non-repudiation, detectability, disclosure, unawareness, non-compliance. One threat and one control each.

| LINDDUN category | Threat | Control |
|---|---|---|
| Linkability | Cross-purpose linking of pseudonyms | Per-purpose HMAC keys |
| Identifiability | Re-identification via quasi-identifiers | Aggregation + small-cell suppression |
| Non-repudiation | User cannot deny (privacy harm) | Review reason codes; do not over-log |
| Detectability | Presence inferable from timing | Batching + jitter on analytics |
| Disclosure | Excess data in logs | Log scrubbing; schema data_class |
| Unawareness | User not told | Plain-language notices |
| Non-compliance | Missing record | ROPA + retention schedule |

### 1.13 Governance framework

- **RACI:** DPO, CISO, Risk owner, Model owner, Compliance owner.
- **Model risk governance:** model card, approval gate, periodic review.
- **Change control:** PR + approval for policy bundles and models.
- **Risk acceptance:** residual risk signed by a named role.
- **Incident response plan:** detect → triage → contain → eradicate → recover → review.
  - Breach clock: GDPR Art. 33 — 72 h to authority; Art. 34 — data subjects if high risk.
  - Card-data incident: acquirer/card brands notified (check contracts).
  - Tabletop exercise (§7 demo).

## 2. Decisions and Trade-offs

| Decision | Choice | Why | Trade-off |
|---|---|---|---|
| DSAR approach | Event-driven fan-out from Privacy Service | Each service knows its own data, no central copy | Slowest service sets the deadline; tracking required |
| Backup deletion | Rolling expiry + re-apply on restore | Editing backups isn't practical | Short window where deleted data survives in backup (documented) |
| Anonymisation vs pseudonymisation | Pseudonymisation default; anonymisation only for aggregates | True anonymisation is a very high bar | Pseudonymised data remains personal data → controls apply |
| Feature retention | Short TTL (e.g., 12 months) with justification | Minimisation | Model learns fewer long-term patterns |
| Differential privacy | Only on published aggregates | Util + privacy balance | Noise reduces accuracy; not applied to individual scoring |
| Consent for fraud | No — legitimate interests | Fraudster won't consent | LIA and objection route must be maintained |
| Governance weight | Lightweight RACI + gates, no committee | Small team | Less formality → keep evidence in Git |

## 3. Diagrams (draw.io)

| Diagram | File |
|---|---|
| Data residency map | `5.2-data-residency.drawio` |
| DSAR sequence | `5.3-dsar-sequence.drawio` |
| Privacy-by-design lifecycle | `5.4-privacy-lifecycle.drawio` |
| RACI + IR timeline | `5.5-raci-ir-timeline.drawio` |

Notes:
- Residency: three cells, each with C2 stores + per-cell KMS. Only allow-listed C1 arrows cross (globe icon, transfer basis tag). Same-zone DR cell dotted.
- DSAR: Requester → Privacy Service (identity check) → Kafka `dsar.requested` → Order, Risk, Compliance, Supply Chain, Support stores → `dsar.completed` → response. Timer "≤1 month".
- Lifecycle: collect → use → share → retain → delete, each stage controlled (minimise, purpose tag, allow-list, TTL, erasure).
- IR timeline: 0 h detect, 72 h authority notice marker.

## 4. Security, Privacy, and Controls

- Purpose tags in schema; access policy purpose-aware (fraud data doesn't go to marketing).
- DSAR data export encrypted, time-limited link, identity verification required.
- Access logging for personal data reads; anomaly alert on bulk access.
- Staff training + confidentiality; masking in support tools.
- Vendor DPAs, sub-processor list, audit rights.

## 5. Failure Scenarios

| Scenario | Behaviour |
|---|---|
| DSAR deadline risk (one service slow) | Dashboard pending steps, escalation, documented extension if justified |
| Deletion incomplete (one store missed) | Automated reconciliation job vs data inventory; gap report |
| Breach in one cell | Cell isolate, keys rotate, 72 h clock starts, affected-subject assessment |
| Misclassified field replicated | CI + runtime detector; replicated copy purge; incident record |
| Biased model detected | Promotion blocked, rollback, retrain, fairness report |
| Cross-border transfer mechanism invalid (legal change) | Transfer register identifies affected flows; shift to regional processing or alternative mechanism |

## 6. Examiner Questions

**Q: Where does pseudonymised data fit in GDPR?**
Strong: "Pseudonymised data is still personal data because re-identification is possible, so all GDPR obligations apply. Pseudonymisation is a security and minimisation measure (Art. 25, 32), not anonymisation. Only truly anonymous aggregates may fall outside scope."
Weak: "If it's hashed, GDPR doesn't apply."

**Q: How do you meet the DSAR deadline, especially in backups?**
Strong: "Privacy Service collects data from all services via events, with a deadline-tracking dashboard. Selective delete in backups isn't practical, so rolling expiry plus re-apply deletion after restore, and that policy is documented."
Weak: "We delete manually."

**Q: How do you check for bias in the fraud model?**
Strong: "Segment-wise false-positive and false-negative rates compared (country, device type, etc.), before promotion and periodically. If the gap exceeds a threshold, the model is held, and human review and appeal are available for affected users. Limitation: protected attributes often aren't available, so proxy segments are used."
Weak: "The model is objective, it has no bias."