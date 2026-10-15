# PCI DSS Scoping

## Scope strategy decision

See `docs/adr/0002-pci-scope-strategy.md` for the ADR.

## Step 1 — Where is account data?

| Location | Stored | Processed | Transmitted | Notes |
|---|---|---|---|---|
| Browser (hosted fields) | No | No | Yes (to PSP) | PSP iframe; platform never sees PAN |
| PSP | Yes (vault) | Yes | Yes | Out of platform CDE |
| Token mapping service | Token only | Token only | Token only | In scope as connected system |
| Checkout service | Token only | Token only | Token only | In scope as connected system |
| Fraud scorer | Token only | Token only | Token only | In scope as connected system |
| Logs / events / analytics | Must never see PAN or CVV | — | — | DLP enforced |

## Step 2 — CDE boundary

- **Inside CDE:** PSP iframe, PSP vault (out of platform).
- **Connected systems (in scope):** token mapping service, checkout page serving scripts.
- **Not in scope, but must not contaminate:** all other platform services.

## Step 3 — PCI scope diagram v0

See `docs/diagrams/1.3-pci-scope-v0.drawio` (to be drawn).

Elements:
- Browser with PSP-hosted-fields iframe (separate bordered zone).
- Platform zone: checkout, token mapping, fraud scorer — labelled "token only" on all internal arrows.
- Red dashed boundary around PSP.
- Green dashed boundary around connected systems; label: "Scripts here are in PCI scope (Req. 6.4.3, 11.6.1)."
- "No PAN" stamp on every internal arrow.

## Step 4 — SAQ expectation

With PSP-hosted capture and no PAN reaching platform servers, the target SAQ is **A or A-EP**, depending on integration details. Confirm with the acquirer/QSA. Even in SAQ A, obligations remain for:

- Payment-page script integrity (Req. 6.4.3, 11.6.1).
- Service-provider management.
- Logging of access to connected systems.

## Step 5 — Scope as living artifact

Reviewed at least every 12 months (Req. 12.5.2) and on any architecture change that moves account data.