# Security, Compliance, and Privacy Controls (Phase 2)

| Control | Linked ADR / requirement |
|---|---|
| Default-deny network policy; mTLS everywhere | ADR-0010; PCI Req. 1, 4 |
| PAN never in platform; CSP and script inventory on checkout page | ADR-0002; Req. 6.4.3, 11.6.1 |
| Regional cells; cross-cell allow-list | ADR-0006; GDPR Art. 44–49 |
| Field-level encryption plus per-cell keys (KMS/HSM-backed); key never leaves region | ADR-0006; Art. 32 |
| Schema classification tags enforced in CI | ADR-0007; Art. 25 |
| Signed policy bundles, signed images, SBOM | ADR-0013; supply-chain security |
| Human review route and appeals | ADR-0008; Art. 22 |
| Audit log of every automated decision and rule/model version | FR-CMP-06, Art. 5(2) |
| Least privilege and MFA for admin access | ADR-0014; Req. 7, 8 |