# Data Classification Scheme

| Class | Examples | Residency | Encryption | Retention rule | Allowed in logs/events? |
|---|---|---|---|---|---|
| **C3 Restricted** | PAN, CVV (never stored), credentials, secrets | Never held by platform (PSP-side) | PSP vault / HSM | CVV: none after authorisation | **Never** |
| **C2 Confidential (personal)** | Name, address, email, phone, device IDs, IPs, order history, behavioural data | In-region only | Field-level + at rest | Purpose-based timers (e.g., fraud features 12-24 months, justified in DPIA) | Pseudonymised only |
| **C1 Internal** | Model features (pseudonymised), custody events (hashed refs), screening outcomes | Region-tagged; can aggregate | At rest | Per policy; audit records ≥ retention law | Yes |
| **C0 Public** | Product catalogue, public tracking status | None | TLS in transit | None | Yes |

## Key rules

- **Classification is a tag on the event schema** (Phase 4), so policy is machine-enforceable, not just documented.
- **Pseudonymisation ≠ anonymisation.** Pseudonymised data is still personal data under GDPR. Only truly anonymised data falls outside it — a high bar.

## Residency map

See `docs/diagrams/1.4-data-residency.drawio`.

- Three region boxes (EU, US, APAC/ME), each containing C2 data stores.
- Cross-region arrows: C1 aggregates / hashed signals only, with globe icon and transfer-basis tag.
- No arrow carries C2 or C3 between regions.