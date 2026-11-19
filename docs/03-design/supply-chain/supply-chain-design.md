# Phase 3C: Supply Chain Visibility & Logistics Security

**Roles:** Blockchain/IoT Engineer (lead), Architect, ML Engineer (anomaly)
**Requirements:** FR-SCV-01 to FR-SCV-05, PRV-04, NFR-05, NFR-06
**ADRs:** ADR-0009 (Fabric custody evidence only)
**Risks:** R-07 (IoT spoofing), R-10 (ledger/ML complexity)

## 1. Tasks

### 1.1 Event model

Custody events: `PICKED_UP`, `HANDED_TO_CARRIER`, `CUSTOMS_CLEARED`, `OUT_FOR_DELIVERY`, `DELIVERED`, `EXCEPTION`.

Each event: shipment ID, actor org, timestamp, location (coarse), reference to off-chain document.

### 1.2 Fabric network design

| Element | Choice |
|---|---|
| Organisations | Platform, Seller consortium, Carriers, Customs brokers |
| Channel | One per corridor (e.g., EU-ME) |
| Ordering | Raft |
| CA | One per org |
| Private data | Private data collections when only two parties should see details |

### 1.3 Chaincode

Functions: `RecordCustodyEvent`, `GetShipmentHistory`, `VerifyEvent`.

Rules:
- Only the current custodian can hand over.
- Timestamps must be monotonic.
- Previous event hash is chained.
- Store **salted hash + reference only** (PRV-04).

### 1.4 Ledger-gateway abstraction

Supply Chain Service calls a ledger-agnostic API. Fabric can be swapped for a signed append-only log (ADR-0009). **A ledger with one writer is theatre.**

### 1.5 MQTT ingestion

Topic taxonomy: `cell/{region}/shipment/{id}/{gps|temp|door|shock}`.

- Mutual TLS with per-device X.509 certificate.
- ACLs: device can publish only on its own topics.
- QoS 1.
- Broker bridges to Kafka.

### 1.6 Cold-chain rules

Configurable limits per product class (e.g., 2–8 °C). **Alert on breach duration, not a single reading**, to reduce noise.

### 1.7 Anomaly detection

| Signal | Method |
|---|---|
| Geofence + route deviation | Rules vs planned corridor |
| Dwell time anomaly | Rules vs hub SLA |
| Sensor plausibility | Impossible speed, GPS jump, flat-lined temperature (spoofing hint) |
| Model | Rules first, plus isolation forest or small autoencoder on telemetry windows |

### 1.8 Counterfeit signals

Serialised IDs (GS1-style): duplicate serial scanned in two places, scan from unexpected region, serial never issued by brand, scan velocity too high. **Flag and raise a case.** Cannot detect a perfect clone with a valid unique serial — needs physical authentication.

### 1.9 Anchoring

Periodically write a **Merkle root** of telemetry batches to the ledger. Raw telemetry stays off-chain; you can prove it wasn't altered later.

## 2. Decisions and Trade-offs

| Decision | Choice | Why | Trade-off |
|---|---|---|---|
| What goes on-chain | Custody events + telemetry Merkle roots | ~1,700 msg/s would overwhelm ledger + leak data | Raw telemetry needs its own integrity controls |
| Channels | One per corridor, private data for two-party details | Selective visibility (FR-SCV-05) | More channel management |
| Ordering | Raft | Simple, crash-fault tolerant | Not Byzantine tolerant — acceptable for known consortium |
| Device auth | Per-device cert + topic ACLs | Stops spoofing by simple credential theft | Cert lifecycle + revocation effort |
| Telemetry store | Time-series DB (e.g., TimescaleDB) in-cell | Query-friendly, region-bound | Another datastore |
| Anomaly approach | Rules first, ML second | Explainable, cheap, works with little data | Rules need upkeep |
| Carrier onboarding | REST API + signing SDK, not full Fabric peer | Carriers rarely run peers | Platform signs on their behalf unless they hold keys (weaker non-repudiation — state it) |

## 3. Diagram: Supply Chain Component View (C4 L3)

See `docs/diagrams/3.3-supply-chain-components.drawio`.

- **Left:** IoT devices → MQTT broker (mTLS, ACLs) → Kafka bridge → Stream processor (rules + anomaly) → TimescaleDB.
- **Centre:** Supply Chain Service (Custody API, Ledger Gateway, Anomaly Handler, Counterfeit Checker, Merkle Anchor job).
- **Right:** Fabric (Platform peer, Carrier peer, Seller peer, Raft orderers, CAs) with chaincode box. **"Hashes only" label.**
- **Red:** device trust boundary.
- **Arrow:** anomalies → Case Management.

## 4. Security, Privacy, and Controls

- Device identity: certs from internal CA, revocation + short rotation. Provisioning in secure step, never shared secrets.
- Plausibility checks: a valid device can still lie. Cross-check GPS with carrier scan events.
- Location precision reduced for non-custodian viewers (data minimisation). Driver/recipient personal data stays off-chain.
- Fabric MSP roles limit who can invoke which chaincode function. Chaincode reviewed, tested, signed.
- Erasure: delete off-chain record + salt → on-chain hash unlinkable.

## 5. Failure Scenarios

| Scenario | Behaviour |
|---|---|
| Fabric peer/orderer down | Queue events off-chain, commit on recovery. Raft tolerates minority loss |
| MQTT broker down | Devices buffer locally, clustered broker, replay on reconnect |
| Sensor spoofing | Plausibility rules + cross-check with scan events raise alert |
| Device cert compromised | Revoke, quarantine topic, flag shipments for review |
| Carrier offline | Event retried with idempotency keys, no duplicates on ledger |
| Consortium member leaves | Channel membership update, historic data stays verifiable |

## 6. Examiner Questions

**Q: Why not store IoT data on the blockchain?**
Strong: "Volume and privacy. Telemetry is high-frequency and potentially personal. I keep it in a time-series store and anchor Merkle roots on the ledger, which proves integrity without the cost or exposure."
Weak: "Blockchain is secure, so everything goes there."

**Q: Blockchain proves the data was recorded, not that it was true. How do you handle garbage-in?**
Strong: "Correct — the ledger gives tamper-evidence, not truth. I add device authentication, plausibility checks, and cross-validation with independent scans. I also state that physical-world trust remains a residual risk."
Weak: "The blockchain makes data trustworthy."

**Q: How do you detect counterfeits?**
Strong: "Serialised identifiers plus anomaly signals: duplicate serials in different places, scans from unexpected regions, unissued serials, unusual scan velocity. It raises cases for human review. It cannot detect a perfect clone with a valid unique serial, which needs physical authentication."
Weak: "AI detects fake products."