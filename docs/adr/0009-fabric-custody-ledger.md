# ADR-0009: Hyperledger Fabric for custody evidence only, with PII off-chain

- **Status:** Accepted
- **Date / Owner:** Phase 2 / Architect + Blockchain/IoT Engineer

## Context

FR-SCV-01/05, PRV-04, conflict C2, R-10.

## Options considered

1. No ledger: database with audit table.
2. Append-only database with hash-chaining and external witness.
3. **Fabric permissioned ledger.**
4. Public chain.

## Honest analysis

On the generic matrix, (1) and (2) often win on cost, operability, and latency. A ledger is justified **only** when multiple mutually distrusting organisations (seller, carrier, customs broker, platform) must write and verify shared history so that no single operator can alter it unnoticed.

## Decision

Choose **option 3, narrowly scoped.** Fabric stores custody-transfer events as salted hashes plus references, one channel per corridor or consortium. Everything else — PII, documents, telemetry, screening data — stays off-chain.

## Consequences

- **Positive:** tamper-evidence, shared truth, selective visibility (channels, private data collections).
- **Negative / debt accepted:** operational complexity (peers, orderers, chaincode lifecycle, CA), limited throughput vs a database, onboarding burden for carriers.
- **Risks and mitigations:** ledger-agnostic API in the Supply Chain Service so Fabric can be replaced by option 2. Small, well-known topology (e.g., Raft ordering). Verify current Fabric release and ordering options.

## Privacy detail

Per-record random salts; avoid hashing low-entropy fields alone; erasure removes off-chain data and salt.

## Revisit trigger

If the consortium does not materialise (only the platform writes), downgrade to option 2 — a ledger with one writer is theatre.