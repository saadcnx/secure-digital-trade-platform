# Regulatory Matrix → Architectural Consequences

**Accuracy note:** article and requirement numbers are cited from memory of the primary texts. Verify each against the source (EUR-Lex for GDPR, PCI SSC Document Library for PCI DSS v4.0.1, Treasury for OFAC) before it goes into an attested deliverable. Trade/e-commerce rules change fast; no specific figures given. That volatility is itself a justification for rules-as-code.

## 1. Payments — PCI DSS v4.0.1

| Req. area | Obligation (paraphrased) | Architectural consequence | Control |
|---|---|---|---|
| Req. 3 | Minimise stored account data; render stored PAN unreadable; never retain sensitive authentication data after authorisation (3.3.1) | Tokenization at the edge; no PAN or CVV in any internal store, log, or event | Token service; log scrubbing; DLP checks |
| Req. 4 | Strong cryptography for PAN over open public networks | TLS 1.2+ (prefer 1.3) everywhere; mTLS internally | Service mesh, cert-manager |
| Req. 6 | Secure development; protect public-facing web apps; manage payment-page scripts (6.4.3) and detect tampering (11.6.1) | CSP and script inventory on checkout page; SAST/SCA gates | CI/CD gates, CSP monitoring |
| Req. 7-8 | Least privilege; MFA for access into the CDE (8.4.2) | RBAC/ABAC; MFA on admin and CDE access | Keycloak, Vault policies |
| Req. 10 | Log and monitor all access to system components and cardholder data | Central tamper-evident logging | Log pipeline with integrity protection |
| Req. 11-12 | Regular testing; documented scope reviewed at least every 12 months (12.5.2); targeted risk analyses | Scope diagram as living artifact; scheduled scans | Pipeline scans; scope-review runbook |

## 2. Privacy

| Source | Obligation | Architectural consequence | Control |
|---|---|---|---|
| GDPR Art. 5 | Lawfulness, purpose limitation, minimisation, accuracy, storage limitation, integrity/confidentiality, accountability | Purpose-tagged data, retention timers, access logging | Data catalogue; TTL jobs |
| Art. 6 | Lawful basis per purpose | Document: fraud prevention (legitimate interests, with LIA), sanctions (legal obligation), payment (contract) | Lawful-basis register |
| Art. 22 | Right not to be subject to solely automated decisions with legal or similarly significant effect | Human review and appeal for blocks and account closures | Review queue; appeal workflow |
| Art. 25 | Data protection by design and by default | Pseudonymised features; regional cells | Design review gate |
| Art. 28 | Processor contracts | DPAs with PSPs, carriers, cloud | Contract register |
| Art. 30 | Records of processing | Maintained ROPA | GRC repository |
| Art. 32 | Security appropriate to risk | Encryption, pseudonymisation, resilience, testing | Security architecture (Phase 5) |
| Art. 33-34 | Breach notification (72 h to authority; data subjects if high risk) | Detection and IR runbooks with timers | SIEM; IR plan |
| Art. 35 | DPIA for high-risk processing | Full DPIA before go-live | DPIA (§ separate file) |
| Art. 44-49 | Transfers outside the EEA need a mechanism | Keep personal data in-region; where transfer needed, SCCs plus TIA | Transfer register; TIA |
| Art. 15-21 | Access, rectification, erasure, restriction, portability, objection | Subject-request orchestration across all stores | DSAR service |
| CCPA/CPRA | Rights to know, delete, correct, opt out of sale/sharing, limit sensitive PI use | Same DSAR service with a US profile; "do not sell/share" signal handling; fraud/security exemptions documented | DSAR service; consent signals |

## 3. Trade and compliance

| Source | Obligation | Architectural consequence | Control |
|---|---|---|---|
| OFAC (US) | Prohibits dealings with SDN-listed persons; strict liability; 50 Percent Rule | Screening must cover ownership; keep ownership fields and review path | Screening engine + ownership checks |
| EU, UN, UK lists | Parallel regimes with different scopes | Multi-list ingestion with per-list provenance and timestamps | List ingestion pipeline |
| US BIS lists (Entity List, DPL, UVL, CSL) | Export-control restrictions | Include in screening scope; end-use/end-user flags | Rules per jurisdiction |
| WCO Harmonized System | 6-digit common classification, revised periodically | HS data versioned; reclassification job on edition change | Versioned classification data |
| WCO Data Model + SAFE Framework | Standardised customs data elements; supply-chain security | Align event and document schemas to WCO data elements | Schema mapping |
| WCO cross-border e-commerce framework | Advance electronic data, risk management, facilitation | Pre-arrival data capture; risk-based clearance support | Pre-advice API |
| WTO Trade Facilitation Agreement | Electronic documents, transparency, risk management | Digital-first documentation | Doc validation service |
| Valuation, origin, import VAT/duty rules | Vary by destination; change often | Rules-as-code with effective dates | Policy repository + tests |

## 4. Other obligations worth a row each

| Source | Why include it |
|---|---|
| PSD2 SCA (EU) | Drives step-up design and exemptions (low-risk transaction analysis can support exemptions) |
| EU AI Act | Assess fraud detection against Annex III — do not assume; document assessment |
| Fake-review rules (EU consumer law; US FTC rule) | Legal basis for review-integrity feature |
| Platform tax reporting (e.g., DAC7) | Awareness that marketplaces carry reporting duties |
| Stricter data regimes (PIPL, India DPDP) | "What if we add this corridor?" test of regional-cell design |

## Flag column

Every row should carry a **"Needs legal/QSA verification"** flag if the obligation is asserted, not attested. Architects design for compliance; they do not interpret or attest it.