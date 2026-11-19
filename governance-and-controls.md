# Global Trade Platform — Governance and Controls

## Document status

- Project type: Educational proof-of-concept
- Environment: Ubuntu EC2, local Python services, local Docker containers
- Data: Synthetic test data only
- Payment status: No payment authorization or settlement
- Compliance status: Not PCI-DSS certified; not a GDPR compliance assessment
- Sanctions/tariff data: Demonstration data only, not official or live lists/rates

## 1. Data classification

| Data type | Demo handling | Production direction |
|---|---|---|
| Test payment number | Only published payment-provider test PAN accepted | Use PSP hosted fields/tokenization; avoid receiving PAN |
| CVV | Not collected or stored | Never store after authorization |
| Customer name/email/phone/address | Synthetic data in local regional SQLite simulation | Approved regional stores, access policy, encryption, retention |
| Fraud features | Amount/country/device signals | Minimize features; document purpose and retention |
| Shipment telemetry | Synthetic MQTT messages | Device identity, signed telemetry, TLS, authorization |
| Audit events | Demo deletion counts and request reference | Central protected audit system and monitored retention |

## 2. Payment handling procedure

1. Use only the published provider test card in this educational demo.
2. Never enter real card numbers or CVV.
3. The demo AES-GCM vault is not a production card vault.
4. Production checkout should use provider-hosted fields/tokenization and provider authorization.
5. Keep payment tokens separate from direct customer identifiers.
6. Do not log PAN, CVV, API keys, JWTs, or encryption keys.
7. Investigate failed or unexpected payment-service responses; do not silently approve.

## 3. Privacy and regional routing procedure

1. Collect only data required for the stated business purpose.
2. Route records according to an approved jurisdiction and data-residency policy.
3. Apply PII redaction before analytics; verify output and account for detector misses.
4. Treat pseudonymous identifiers as potentially personal data.
5. Restrict access, define retention, encrypt storage, and protect backups.
6. Process erasure requests only after appropriate identity and authorization checks.
7. Record the request reference, action, timestamp, and outcome without copying unnecessary PII.
8. Assess backups, caches, replicas, and lawful retention separately.

The local SQLite region labels are simulated and do not establish geographical residency.

## 4. Sanctions and export-control procedure

1. The included list and policy rules are synthetic educational examples.
2. Do not approve or reject a real transaction based on this prototype.
3. A production system requires authoritative, current data sources and documented update checks.
4. Fuzzy matches should create a review/hold workflow; similarity alone is not proof of identity.
5. A trained compliance reviewer must resolve potential matches using approved procedures.
6. Escalate confirmed or suspected matches according to the organization's legal and compliance process.
7. Validate jurisdiction, product classification, license requirements, and transport rules with qualified specialists.

## 5. Incident response: suspected fraud / sensor anomaly

1. Preserve the event ID, timestamp, transaction/shipment reference, and relevant system logs.
2. Avoid copying raw card data or unnecessary personal data into incident tickets.
3. For a high-confidence fraud signal, block or step up according to approved policy.
4. For a shipment temperature/seal anomaly, notify the responsible logistics operator.
5. Verify sensor identity and telemetry integrity; a blockchain record alone does not prove sensor truth.
6. Record decisions, owner, time, and recovery action.
7. Escalate data incidents using the organization's approved incident-response and privacy processes.

## 6. Security and deployment controls

- Restrict SSH to trusted administrator source addresses.
- Keep application, MQTT, and Fabric demo ports private.
- Use least-privilege identity and short-lived credentials in production.
- Store production secrets in an approved secret-management service.
- Require tests and security scans before deployment.
- Review scan findings and document accepted risks.
- Back up data according to approved retention and recovery policy.
- Monitor service health, access, failed authentication, and security alerts.

## 7. Architectural trade-offs

### Synchronous checkout checks
Fraud and trade-compliance checks are synchronous in this prototype so a decision is returned during checkout. A production system must define timeouts, service-level objectives, retries, circuit breakers, and a fail-closed or review policy.

### Asynchronous shipment updates
Shipment telemetry and ledger updates can be processed asynchronously so ledger latency does not unnecessarily delay checkout. The producer needs durable buffering, retry, deduplication, dead-letter handling, and operational monitoring.

### False positives
A fuzzy sanctions match is a screening signal, not proof. Borderline matches should be placed on hold for authorized human review. Fraud medium risk should trigger a genuine provider step-up challenge; this demo does not implement OTP or 3DS.

### Prototype boundaries
The current services run on one host and use local files/containers. This is not a highly available, regionally isolated, production-secure, or certified deployment.

## 8. Recovery objectives for the proposed design

The following are design targets to be agreed and tested—not measured guarantees from this prototype:

- Checkout decision availability: define service-specific timeout and fail-closed behavior.
- Shipment event recovery: use a durable queue, retry policy, idempotency key, and dead-letter queue.
- Recovery point objective (RPO): define acceptable loss for each data class.
- Recovery time objective (RTO): define and test restoration procedures.
- Key recovery: follow approved key backup/rotation and access procedures.
