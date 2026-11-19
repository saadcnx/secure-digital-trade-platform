# Phase 5A: Threat Modelling, Identity, Cryptography & PCI Controls

**Roles:** Architect (lead), Payments/Security Engineer (lead on controls), DevSecOps, GRC
**Requirements:** FR-PLT-01, SEC-*, NFR-08, REG (PCI Req. 3, 4, 6, 7, 8, 10, 11)
**ADRs:** ADR-0006 (regional cells), ADR-0007 (schema classification), ADR-0011 (control plane)
**Risks:** R-01, R-04, R-07, R-09

**Accuracy flag:** PCI requirement numbers below are from memory (v4.0.1). Verify against the primary document before use in an attested deliverable.

## 1. Tasks

### 1.1 STRIDE per trust boundary (TB1–TB8)

| Boundary | Key threat | Control | Residual |
|---|---|---|---|
| TB1 Internet → Edge | Bot floods, credential stuffing (S, D) | WAF, rate limit, bot defence, MFA, breached-password check | Low-and-slow attacks — accept with monitoring |
| TB2 Edge → Mesh | Token theft, spoofed service (S, E) | OIDC validation, mTLS, short token TTL | Stolen valid token within TTL |
| TB3 Mesh → Restricted tier | Lateral movement, data theft (I, E) | Default-deny, per-service identity, MFA, dynamic DB credentials | Insider with legit access |
| TB4 Cell ↔ Control plane | Malicious policy/model push (T, E) | Signed artefacts, cells verify, last-known-good | Signing key compromise |
| TB5 Cell ↔ Cell | Personal data leak (I) | Allow-list, CI policy, no C2 topics | Misclassified schema |
| TB6 Platform ↔ External | Webhook forgery, replay (S, T, R) | Signature, timestamp, nonce, adapters | PSP-side compromise |
| TB7 Device → MQTT | Device spoofing, replay (S, T) | Device certs, topic ACLs, plausibility checks | Physically tampered genuine device |
| TB8 Platform ↔ Fabric | Rogue org, chaincode abuse (T, R, E) | MSP roles, chaincode review and signing | Collusion among members |

STRIDE under-covers privacy; a LINDDUN-lite pass is in Phase 5B.

### 1.2 Abuse cases (attacker's view)

| Case | Attacker goal | Primary control |
|---|---|---|
| Card testing | Validate stolen cards cheaply | Velocity limits, CAPTCHA on risk, small-amount auth alerts |
| Credential stuffing | ATO at scale | Bot defence, MFA, breached-password check, impossible-travel |
| ATO | Account hijack | MFA risk-based, session binding, new-device step-up |
| Model poisoning | Skew fraud decisions | Registry write-restrict, training-data validation, signed artefacts |
| Sensor spoofing | Fake custody evidence | Device certs + plausibility + cross-check with scan events |
| Sanctions evasion | Slip past screening | Multi-list + ownership field + normalisation + review |
| Webhook replay | Duplicate payment events | Signature, timestamp, nonce, idempotency |
| Insider misuse | Bulk data export | JIT admin, session recording, anomaly alert on bulk access |
| Control-plane compromise | Push malicious policy/model | Signed artefacts, HSM-held signing key, cells hold last-known-good |
| Malicious checkout script | Skim PAN in browser | CSP + SRI + script inventory + tamper detection (Req. 6.4.3, 11.6.1) |

### 1.3 Risk rating

5×5 (likelihood × impact, Phase 1 scale). Top 10 in the risk register with owner.

### 1.4 Identity design

| Actor | Mechanism |
|---|---|
| Users | Keycloak, OIDC Authorization Code + PKCE, MFA risk-based, breached-password check |
| Partners (carriers, sellers) | OAuth2 client credentials + mTLS, scopes limited |
| Admins | MFA mandatory (PCI Req. 8.4.2), JIT access, session recording, sealed and alarmed break-glass |
| Workloads | Mesh identity (SPIFFE-style), short-lived certificates, no static service passwords |
| Authorisation | RBAC for coarse roles; ABAC via OPA for shipment-level and case-level visibility |

### 1.5 Cryptography and key management

- TLS 1.2+ (prefer 1.3) external; mTLS internal.
- Envelope encryption: data keys encrypted by per-cell master keys in KMS/HSM. **Keys never leave the cell.**
- Field-level encryption (e.g., Tink) for C2 fields; token DB and case notes first.
- Rotation schedule; dual control for master-key operations; key inventory.
- Hashing: Argon2id/bcrypt for passwords; HMAC with per-purpose keys for pseudonymisation.
- Signing: Cosign for images; signed policy bundles; signed model artefacts.
- Secrets in Vault, dynamic short-lived credentials for databases.

### 1.6 PCI control implementation

See §3 table. Scope diagram updated with token boundary and connected-system markers.

### 1.7 Logging and detection

- Central tamper-evident logs (append-only, hash-chained or WORM).
- SIEM (Wazuh), runtime detection (Falco).
- Alerts for fraud-of-the-platform (admin anomalies, mass exports).
- Retention 12 months, 3 months immediately available (Req. 10.5.1).

### 1.8 ML-specific security

- Training-data validation.
- Registry write restrictions.
- Model signing.
- Adversarial robustness checks (evasion).
- Rate limits on scoring API to stop model probing.

### 1.9 Traceability

Security architecture diagram and security requirements linked in the RTM.

## 2. STRIDE per Boundary (condensed)

See §1.1 table.

## 3. PCI DSS Control Mapping (verify numbers)

| Area | Control in our design | Evidence |
|---|---|---|
| Req. 1 Network | Default-deny network policies, segmented restricted tier | Policy files, scan output |
| Req. 3 Stored data | No PAN/CVV stored. Token DB only. Log scrubbing, DLP tests in CI | CI report, data-flow review |
| Req. 4 Transmission | TLS 1.2+, mTLS internal | Mesh config, scan |
| Req. 6 Secure dev | SAST/SCA/IaC gates, script inventory + integrity on payment page (6.4.3), WAF or equivalent | Pipeline logs, script register |
| Req. 7-8 Access | RBAC/ABAC, MFA for CDE-adjacent admin (8.4.2), strong password rules | Keycloak config, access reviews |
| Req. 10 Logging | Central logs, integrity protection, time sync, daily review automation, 12-month retention | SIEM config |
| Req. 11 Testing | Scans, penetration test, payment-page tamper detection (11.6.1) | Reports |
| Req. 12 Governance | Scope review at least every 12 months (12.5.2), incident response plan, PSP responsibility matrix | Documents |

**Remember:** hosted fields reduce scope, they don't remove it. Confirm SAQ type with acquirer or QSA.

## 4. Decisions and Trade-offs

| Decision | Choice | Why | Trade-off |
|---|---|---|---|
| Key custody | Per-cell KMS/HSM-backed keys, Vault for secrets | Residency + blast radius | More key operations. Real HSM simulated in demo |
| Field-level vs disk-only | Both; field-level on C2 | Protection from DB admin too | Harder query/index — use blind indexes |
| Admin access | JIT + MFA + session recording | Insider + stolen credential risk | Operational friction |
| Detection stack | Wazuh + Falco (open source) | Constraint fit | Tuning + alert fatigue — alert tiering required |
| Authorisation | RBAC + ABAC (OPA) | Shipment-level visibility needed | Policy complexity, test coverage needed |
| Pseudonymisation | HMAC with per-purpose keys | Purpose separation (fraud vs analytics) | More key management |
| Threat method | STRIDE + abuse cases + LINDDUN-lite | Systematic + privacy covered | Takes more time |

## 5. Diagram: Security Architecture

See `docs/diagrams/5.1-security-architecture.drawio`.

Layers (top to bottom): **Edge** (WAF, gateway, bot defence) → **Identity** (Keycloak) → **Mesh** (mTLS, OPA) → **Services** → **Data tier** (encrypted, field-level) → **Key layer** (KMS/HSM, Vault) → **Detection** (SIEM, Falco) on the side.

TB1–TB8 as red dashed boundaries, each tagged with its control. A separate lane for supply-chain security (signed images, SBOM, signed policies). Key-flow arrow: master key → data key → ciphertext, labelled "keys never leave cell".

## 6. Failure Scenarios

| Scenario | Behaviour |
|---|---|
| Admin credential stolen | MFA + JIT limit reach; session recording; anomaly alert; credential revoked |
| Key compromise (cell key) | Rotate, re-encrypt, isolate cell. Other cells unaffected |
| Control-plane signing key compromised | HSM-held, offline root, cells hold last-known-good, key-rotation runbook |
| SIEM down | Logs buffer, secondary alert path, gap report |
| Model-probing attack | Rate limit, query-anomaly detection, score rounding |
| Webhook forgery | Signature fails, alert, source block |

## 7. Examiner Questions

**Q: What is your biggest threat and why?**
Strong: "Credential stuffing → ATO, and control-plane compromise are top in my risk scoring. ATO has higher likelihood, control plane has higher impact. So bot defence, MFA, and signed artefacts plus cells' last-known-good fallback. Residual risk has an owner in the register."
Weak: "Hackers." Or no ranking.

**Q: Encryption vs tokenisation — difference, and where do you use each?**
Strong: "Tokenisation replaces PAN with a non-derivable surrogate, with the original in the PSP vault. Encryption is reversible if you have the key. For PAN I use tokenisation (scope reduction); for C2 personal data I use field-level encryption; keys live in the cell's KMS/HSM."
Weak: "They're the same."

**Q: How do you handle insider threat?**
Strong: "Least privilege, JIT admin access with MFA, session recording, separation of duties (dual control for keys and policy changes), tamper-evident logs, and anomaly alerts for bulk exports. Residual risk is collusion, reduced by detective controls and audits."
Weak: "We trust employees."