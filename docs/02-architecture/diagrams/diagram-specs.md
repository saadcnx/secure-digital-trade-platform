# Diagram Specs (draw.io)

## Diagram 2.1: Capability map
Four horizontal bands (Fraud & Trust, Trade Compliance, Supply Chain Visibility, Payments) plus Platform & Governance beneath. Each band holds 4–6 capability boxes. Colour by build / adopt / buy.

## Diagram 2.2: C4 Level 1 — System context (refined)
Centre: **Secure Digital Trade Platform**. People: Buyer, Seller, Fraud Analyst, Compliance Officer, DPO/Auditor, Carrier user. External: PSP/acquirer, 3-D Secure/issuer, sanctions list publishers, customs/tax interfaces, carrier & IoT devices, identity federation. Annotate arrows with data class (C1/C2); globe icon on cross-jurisdiction arrows. Note: "Card data flows browser → PSP only."

## Diagram 2.3: C4 Level 2 — Containers (one cell)

| Zone | Containers |
|---|---|
| **Edge** | WAF, API Gateway (APISIX/Kong), bot-defence filter |
| **Identity** | Keycloak |
| **Core services** | Checkout/Order, Payment Orchestrator, Risk Decision, Compliance, Supply Chain, Privacy, Case Management |
| **Streaming & data** | Kafka + Schema Registry, stream processor (features), Redis, PostgreSQL per service, object storage |
| **IoT** | MQTT broker (EMQX/Mosquitto) → Kafka bridge |
| **Ledger** | Fabric peer(s), CA, chaincode |
| **ML** | Feast, training jobs, MLflow registry |
| **Ops** | Prometheus/Grafana/OTel, SIEM (Wazuh), Vault, Argo CD |

Solid arrows = synchronous; dashed arrows through the Kafka bar = asynchronous. Mark **checkout critical path** in red.

## Diagram 2.4: Global topology (cells + control plane)
Three cell boxes (EU, US, APAC/ME) each containing the cell stack, inner label "C2 stays here". Above: **Global Control Plane** (policy bundles, model registry, config, aggregate dashboards). Arrows **down** for policy/models; **up** for aggregates and hashed signals only. Label: "No C2/C3 upward." Optional EU-2 DR cell with note "DR stays within residency zone."

## Diagram 2.5: Deployment topology
Per cell: cloud account → VPC with three subnets (public edge, private services, restricted data/token tier), K8s across 3 AZs, Fabric peers on dedicated nodes, KMS/HSM service, object storage with regional lock. Network policies as arrows with "deny by default" annotation; mesh mTLS as coloured overlay.

## Diagram 2.6: Checkout sequence with fallback (C4 Dynamic)
Browser (hosted fields → PSP, token returned) → Gateway → Checkout → **Risk Decision (≤100 ms)** → decision tier → Payment Orchestrator (3DS if step-up) → Order accepted → async: Compliance screening → hold or release → custody event. Alternative branch: "Risk timeout → local rules fallback → tiered decision."

## Diagram 2.7: Decision map
One-page graph of ADRs 0005–0015 with dependency arrows (e.g., ADR-0006 → ADR-0007, ADR-0015; ADR-0009 → ADR-0006 for channel/cell mapping), coloured by status. Use as presentation anchor.