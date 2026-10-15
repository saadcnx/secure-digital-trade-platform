# ADR-0014: Identity and access

- **Status:** Accepted
- **Date / Owner:** Phase 2 / Architect + Security Engineer

## Decision

**Keycloak** (OIDC/OAuth2) for users, partners (carriers), and admins, with **MFA** for privileged and CDE-adjacent access (PCI Req. 8.4.2). **Workload identity** via the mesh (SPIFFE-style IDs). Authorisation by **RBAC** for coarse roles plus **ABAC** through OPA for shipment-level visibility (FR-SCV-05).

## Consequences

- **Positive:** mature open-source identity; supports multiple audiences; policy externalised.
- **Negative / debt accepted:** Keycloak is powerful but operationally heavy.

## Revisit trigger

Keycloak upgrade or HA burden outweighs customisation value → consider a managed identity service in-region (with more lock-in and less control).