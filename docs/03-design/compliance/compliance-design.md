# Phase 3B: Trade Compliance Design

**Roles:** Compliance/Trade Engineer (lead), Architect, GRC
**Requirements:** FR-CMP-01 to FR-CMP-06, NFR-03, NFR-04
**ADRs:** ADR-0010 (zero-trust mesh), ADR-0013 (policy-as-code)
**Risks:** R-02 (sanctioned-party false negative), R-03 (stale list)

## 1. Tasks

### 1.1 List ingestion pipeline

Pull official feeds on schedule:

| List | Source | Schedule | Format |
|---|---|---|---|
| OFAC SDN / Consolidated | treasury.gov | 4 h | XML/CSV |
| EU Consolidated | EUR-Lex | 4 h | XML |
| UN Consolidated | un.org | 6 h | XML |
| UK OFSI | gov.uk | 4 h | CSV |
| BIS Entity List, DPL, UVL, CSL | bis.doc.gov | 24 h | CSV |

Store each entry with source, list version, and timestamp. Normalise names: lowercase, strip diacritics, transliterate, expand aliases and AKAs. **Verify licence and format of each feed.** Aggregators (e.g., OpenSanctions) only after licence check — they may restrict commercial use.

### 1.2 Party model

Screen: buyer, seller, consignee, ship-to, carrier. Optional ownership field supports OFAC's **50 Percent Rule** (entities owned 50%+ by blocked persons are also blocked).

### 1.3 Matching engine (layered)

| Layer | Method | Output |
|---|---|---|
| 1 | Exact match on IDs (passport, tax ID, vessel IMO) | Strong hit → review |
| 2 | Fuzzy name: token-based + Jaro-Winkler or Levenshtein | Score |
| 3 | Phonetic pass for transliteration variants | Score boost |
| 4 | Context boosters: country, DOB, address | Score boost |

Output: auto-clear, review, or hold. Thresholds tunable per list and risk tier.

### 1.4 Case workflow

Review hits → Case Management with evidence. Analyst decides: true match, false positive, whitelist with expiry. Decisions feed back to tune thresholds. **Whitelist entries need an owner and expiry date. No permanent whitelist.**

### 1.5 Document validation

Check commercial invoice completeness (parties, description, value, currency, origin, HS code, Incoterm), consistency (declared value vs order value, origin vs seller country), and destination-specific requirements via OPA.

### 1.6 HS classification assistant

Suggest code from product title/description with confidence score. Low confidence → human review. Human override stored as label. **HS edition versioned; re-map when edition changes.**

### 1.7 Rules as code

Rego policies per jurisdiction (restricted goods, document requirements, thresholds, effective dates). Tests per rule. Signed bundles distributed via control plane. **No hotfix edits in production.**

### 1.8 Audit record per decision

Inputs hash, list versions, rule bundle version, score, outcome, reviewer. Append-only table with periodic hash anchoring (optionally to ledger).

## 2. Decisions and Trade-offs

| Decision | Choice | Why | Trade-off |
|---|---|---|---|
| Matching | Layered exact, fuzzy, context | Names are noisy; exact alone misses variants | Tuning cost + false-positive load |
| Where to screen | Async hold-before-fulfilment, not checkout path | Keeps checkout fast (NFR-02), still stops shipping | Customer may wait if hit needs review |
| Failure mode | Fail-closed for fulfilment (ADR-0010) | Violation is a legal breach | Held orders when service is down |
| Re-screening | Batch re-screen all parties on list change | Existing customers can become listed | Compute spike → queue with priority |
| HS classification | ML suggestion + human override | Misclassification affects duty and legality | Needs labelled data. Start with rules + keyword model, not deep NLP |
| Policy engine | OPA for rules, dedicated service for matching | OPA not built for fuzzy matching over large lists | Two components to operate |
| Data source | Official feeds first, aggregators only after licence check | Authoritative, legally safe | Own normalisation work |

## 3. Diagram: Compliance Component View (C4 L3)

See `docs/diagrams/3.2-compliance-components.drawio`.

- **Left:** Kafka `order.placed` → Compliance Service (Party Extractor, Screening Matcher, Document Validator, HS Suggester, Decision Builder, Audit Writer).
- **Top:** List Ingestion Pipeline (official feeds → normaliser → list store with versions → matcher index).
- **Right:** OPA sidecar (policy bundles from Git via control plane).
- **Bottom:** output events `order.hold`, `order.release`, plus link to Case Management.
- **Red mark:** the hold gate — no fulfilment event without a release.

## 4. Security, Privacy, and Controls

- Screening data is C2 personal data → stays in-cell. Only list data (public) is global.
- Immutable audit trail: append-only + periodic hash anchoring.
- Whitelist: owner + expiry. No permanent whitelist.
- Policy changes: PR review + automated tests + signed bundles.
- Art. 22: automated holds get a review route and plain-language notice, without tipping off where law requires.

## 5. Failure Scenarios

| Scenario | Behaviour |
|---|---|
| Screening service down | Orders accepted, fulfilment held, backlog processed on recovery |
| Stale list | Freshness alert at 1 h, list timestamp shown in every decision, batch re-screen after refresh |
| Over-matching flood | Raise threshold temporarily with CISO + compliance approval, extra reviewers, logged as exception |
| Bad rule bundle | Automated tests block it. Staged rollout. Git revert |
| Missed ownership link | Periodic ownership refresh + sampled manual audit (residual risk, accepted and recorded) |

## 6. Examiner Questions

**Q: How do you reduce false positives without missing true hits?**
Strong: "Layered matching: exact IDs first, fuzzy names with context like country and DOB, tiered thresholds, review queue. I measure false negatives with seeded test entities and track false-positive review time. Thresholds are a business risk decision — compliance owns them."
Weak: "We set a high threshold."

**Q: Why not screen synchronously at checkout?**
Strong: "Checkout has a tight latency and availability budget. The hold-before-fulfilment gate stops the legal risk (shipping) without hurting conversion. Where payment capture itself is restricted, I'd move the check into the sync path for that segment."
Weak: "Screening is too slow."

**Q: A new country rule appears. What do you do?**
Strong: "It's a Rego policy change with tests in Git, signed and rolled out through the pipeline. No service code change. Same for effective dates, so rules can be scheduled."
Weak: "We would update the code."