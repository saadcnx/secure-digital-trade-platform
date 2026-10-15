# ADR-0004: Lawful basis for fraud processing

- **Status:** Accepted
- **Date / Owner:** Phase 1 / DPO (architect-owned)

## Context

Fraud scoring and account security require rich behavioural data. Under GDPR, processing needs a lawful basis per purpose. Consent for fraud detection is unworkable (fraudsters would refuse).

## Purpose-to-basis mapping

| Purpose | Lawful basis | Reasoning |
|---|---|---|
| Fraud scoring and account security | Legitimate interests (Art. 6(1)(f)) with a documented LIA | Recital 47 recognises fraud prevention as a legitimate interest |
| Sanctions screening | Legal obligation (Art. 6(1)(c)) | Mandated by law |
| Payment execution | Contract (Art. 6(1)(b)) | Needed to perform the purchase |
| Marketing analytics | Consent | Not necessary for the service; kept fully separate |

## Decision

Adopt the mapping above. Purpose separation prevents fraud data drifting into marketing use. Provide human review and appeal for any decision with significant effect (Art. 22 safeguard).

## Consequences

- **Positive:** defensible lawful basis; supports purpose limitation; enables objection route.
- **Negative / debt accepted:** LIA must be maintained and reviewed on change of processing.
- **Risks and mitigations:** legitimate interests can be overridden by data subject rights — mitigated by minimisation, retention limits, and review.

## Compliance & security impact

- GDPR Art. 6, 5(1)(b), 22, 25.
- CCPA/CPRA: fraud/security exemptions documented for applicable rights.

## Revisit trigger

Reopen if processing expands to a new purpose, a new category, or a new jurisdiction with a different lawful-basis regime.