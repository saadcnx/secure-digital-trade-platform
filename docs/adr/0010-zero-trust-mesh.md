# ADR-0010: Zero-trust networking with a service mesh

- **Status:** Accepted
- **Date / Owner:** Phase 2 / Architect + Security Engineer

## Context

PCI Req. 1, 4, 7, 8; STRIDE spoofing and tampering; R-01.

## Options considered

1. Perimeter network segmentation only.
2. **Mesh with mTLS and identity-based authorisation.**
3. Application-level TLS per service.

## Decision

Choose **option 2**: Istio (CNCF graduated) with workload identity, default-deny network policies, and OPA for fine-grained authorisation.

## Consequences

- **Positive:** every call authenticated and encrypted without per-team crypto code; policy is auditable.
- **Negative / debt accepted:** sidecar resource cost and complexity (consider ambient mode — verify maturity); debugging difficulty.
- **Risks and mitigations:** **Linkerd** is lighter, but its stable-release distribution model changed (verify), which matters under an open-source constraint.

## Revisit trigger

Mesh overhead breaches the latency budget → fall back to eBPF-based networking (e.g., Cilium) with selective mTLS.