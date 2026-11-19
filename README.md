# Secure Digital Trade & Cross-Border E-Commerce Platform

> **Educational proof of concept.** This repository demonstrates selected open-source security, fraud-detection, privacy, logistics, and DevSecOps concepts. It is not a production payment platform, legal compliance system, or certified PCI-DSS/GDPR implementation.

## Project overview

This project is an educational prototype for a cross-border digital-trade platform. It brings together small modules for:

- Transaction fraud scoring with **XGBoost** and scikit-learn.
- Basic bot and account-takeover behavioural signals.
- Fake-review classification using a scikit-learn text pipeline.
- Demonstration sanctions screening using **RapidFuzz** and sample data.
- Example HS-code/tariff calculations and policy checks.
- Test-card-only tokenization demonstration using **AES-256-GCM**.
- Synthetic shipment telemetry using **Eclipse Mosquitto MQTT**.
- Shipment event recording on a local **Hyperledger Fabric test network**.
- PII detection/redaction using **Microsoft Presidio**.
- Simulated regional data routing with SQLite.
- Python API services built with **FastAPI**.
- Security checks using **pytest**, **Bandit**, **Trivy**, and **OWASP ZAP**.

The system is intended for learning, demonstrations, and architectural discussion. Use synthetic data only.

## Important limitations

This project does **not**:

- Process, authorize, settle, or charge real payments.
- Accept real card data. The payment demo only accepts the published Stripe test PAN `4242424242424242`.
- Store CVV. Do not add CVV collection or storage.
- Establish PCI-DSS compliance or certification.
- Establish GDPR/CCPA compliance or actual geographic data residency.
- Use official, current sanctions lists, tariff rates, or export-control determinations.
- Generate an officially valid WCO/CN23 customs declaration.
- Prove that IoT sensor messages are genuine merely because they are recorded on a ledger.
- Provide production high availability, disaster recovery, service-level guarantees, or automated incident response.

The local SQLite region names are simulations, not physical cloud regions. The sample sanctions, tariff, and policy data are educational examples only. Production decisions must use approved authoritative sources and qualified compliance/legal review.

## Architecture

### Local proof-of-concept architecture

The prototype runs Python services and Docker containers on an Ubuntu host. The checkout orchestrator calls local fraud, compliance, payment-tokenization, and privacy modules. MQTT receives synthetic shipment telemetry. The optional Fabric test network records shipment state.

### Proposed production direction

A production design would require a separately assessed cloud architecture. Potential AWS components may include CloudFront/WAF, API Gateway, ECS/Fargate or Lambda, Step Functions, SQS, AWS IoT Core, KMS, Secrets Manager, CloudTrail, CloudWatch, and approved regional data stores. A payment service provider's hosted fields and tokenization should be preferred over receiving card data in this application.

**The AWS services above are a proposed design, not services deployed by this repository.**

See [`docs/diagrams/`](docs/diagrams/) for architecture and data-flow diagram source files.

## Repository layout

```text
.
├── blockchain_ledger/       # Fabric bridge and chaincode source
├── compliance_engine/       # Demo sanctions, tariff, and policy modules
├── dashboard/               # Minimal local demo page
├── docs/
│   ├── diagrams/            # Mermaid architecture/DFD/workflow diagrams
│   ├── evidence/             # Demo and failure-test notes
│   └── presentation/         # Presentation results template
├── fraud_engine/            # Fraud model, behavioural and review modules
├── iot_logistics/            # MQTT simulator, listener, broker config
├── orchestrator/             # Checkout API
├── payment_vault/            # Test-PAN-only tokenization demo
├── privacy_governance/       # Presidio and local routing simulation
├── tests/                    # Automated tests
├── .env.example              # Secret-free environment template
├── docker-compose.yml        # Local app and MQTT demo
├── Dockerfile
├── requirements.txt
└── README.md
```

Generated model files, local databases, MQTT credentials, and downloaded Fabric samples are intentionally excluded from Git.

## Requirements

Recommended for the complete local demonstration:

- Ubuntu 24.04 LTS.
- Python 3.12.
- Git.
- Docker Engine and Docker Compose plugin.
- At least 8 GB RAM recommended for running the full Fabric test network.
- At least 25–30 GB free disk space recommended for Docker images, Python packages, and Fabric artifacts.
- `curl`, `jq`, and `build-essential`.

The fraud/API/privacy portions need fewer resources than the complete Hyperledger Fabric test network.

## Quick start: Python development environment

From the repository root:

```bash
sudo apt update
sudo apt install -y \
  git curl jq build-essential \
  python3-pip python3-venv python3-dev \
  libssl-dev libffi-dev

python3 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Generate the synthetic fraud dataset and model:

```bash
python fraud_engine/generate_data.py
python fraud_engine/train_fraud_model.py
python fraud_engine/fake_review_detector.py
```

The dataset and model are generated locally and are not committed to Git.

## Configure local demo secrets

Start from the example:

```bash
cp .env.example .env
chmod 600 .env
```

Generate secrets locally and enter them into `.env`. Do not paste them into tickets, chat, screenshots, or GitHub. One option is:

```bash
python - <<'PY'
import base64
import secrets

print("PAYMENT_AES_KEY_B64=" + base64.b64encode(secrets.token_bytes(32)).decode())
print("JWT_SECRET=" + secrets.token_hex(32))
print("DEMO_API_KEY=" + secrets.token_urlsafe(32))
print("PRIVACY_API_KEY=" + secrets.token_urlsafe(32))
print("MQTT_PASSWORD=" + secrets.token_urlsafe(32))
PY
```

Copy the generated values into the corresponding `.env` entries. The generated secrets are displayed in your terminal; keep them private. Do not commit `.env`.

Load variables in a terminal when a service needs them:

```bash
set -a
source .env
set +a
```

## Run the local checkout API

After generating the fraud model and setting up `.env`:

```bash
source venv/bin/activate
uvicorn orchestrator.checkout_api:app --host 127.0.0.1 --port 8000
```

Check health:

```bash
curl -s http://127.0.0.1:8000/health | jq
```

Open API documentation locally at:

```text
http://127.0.0.1:8000/docs
```

The checkout API requires the `X-Demo-API-Key` header and uses synthetic data only. An example request is documented in the project implementation notes; do not use real customer or payment information.

## Run the MQTT demonstration

Create the Mosquitto password file as described in the project setup notes, then start the broker:

```bash
docker compose -f iot_logistics/mosquitto.compose.yml up -d
docker ps --filter name=trade-mosquitto
```

Load `.env`, then run the listener:

```bash
source venv/bin/activate
set -a
source .env
set +a

python iot_logistics/mqtt_listener.py
```

In another terminal, load the same `.env` and run a synthetic sensor:

```bash
cd ~/global-trade-platform
source venv/bin/activate
set -a
source .env
set +a

python iot_logistics/iot_sensor_simulator.py \
  --shipment-id SHIP-DEMO-001 \
  --interval 3 \
  --anomaly-every 5
```

Stop the simulator/listener with `Ctrl+C`. Do not expose the MQTT port to the public internet.

## Hyperledger Fabric

The Fabric test network is a separate optional setup and consumes additional resources. Follow the official Hyperledger Fabric installation instructions and the project’s Fabric setup notes. Downloaded Fabric samples, certificates, wallet files, and generated network material are excluded from Git.

Use only the local test network. Do not expose peer, orderer, or bridge ports publicly. The test network is not a production ledger deployment.

## Docker Compose

Build and start the local app and MQTT services:

```bash
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail 50 app
```

The app is bound to `127.0.0.1:8000`, not to a public interface. Stop the services with:

```bash
docker compose down
```

The local Fabric test network is managed separately.

## Tests and security scans

Run automated tests:

```bash
source venv/bin/activate
pytest -q
```

Run Bandit:

```bash
bandit -r \
  fraud_engine compliance_engine payment_vault \
  iot_logistics blockchain_ledger privacy_governance orchestrator \
  -ll
```

Run Trivy filesystem scan if Trivy is installed:

```bash
trivy fs --scanners vuln,secret,misconfig --severity HIGH,CRITICAL .
```

Run the OWASP ZAP baseline scan only against your own locally running demo service. It is a passive baseline scan, not a penetration test:

```bash
mkdir -p reports

docker run --rm --network host \
  -v "$PWD/reports:/zap/wrk:rw" \
  zaproxy/zap-stable \
  zap-baseline.py \
  -t http://127.0.0.1:8000 \
  -m 2 \
  -r zap-report.html
```

Review findings; do not suppress or ignore them without understanding and documenting the risk.

## Troubleshooting

A detailed error log supplied during development should be kept as:

[`docs/ERRORS-FACED-AND-RESOLVED.md`](docs/ERRORS-FACED-AND-RESOLVED.md)

The recurring issues and general fixes include:

| Area | Typical issue | Checks / guidance |
|---|---|---|
| Shell heredocs | File content accidentally includes later commands or has a broken ending | Use a unique terminator such as `PYEOF` or `GOEOF`; inspect the file with `tail`, `file`, and syntax checks. |
| Mosquitto | Broker refuses connections or repeatedly restarts | Check `docker ps`, `docker logs trade-mosquitto`, broker configuration, password-file path, and file permissions. Load `.env` before starting Python MQTT clients. |
| Python environment | `ModuleNotFoundError` or `python` command not found | Activate `venv`; use `python3` outside the venv; install dependencies in the active environment. |
| Pytest imports | Project package cannot be imported | Run pytest from the project root and add a `pytest.ini` with `pythonpath = .` if needed. |
| Fabric setup | Missing `fabric-samples`, binaries, Go, certificates, or chaincode dependencies | Check installer arguments, Fabric paths, Go installation, `go mod tidy`, and the actual certificate paths before changing scripts. |
| Fabric endorsement | Endorsement policy requires more peers than the CLI command specifies | Inspect the deployed chaincode endorsement policy and provide the required peer addresses and TLS roots. |
| Fabric function mismatch | Bridge calls a function name not implemented by the chaincode | Compare the chaincode's actual transaction names with the bridge query/invoke payloads. |
| Docker port conflict | `address already in use` | Find the existing process/container before stopping it; do not kill an unrelated service blindly. |
| Docker build context | Build is unexpectedly large | Exclude `venv/`, Fabric samples, generated data, databases, caches, and reports using `.dockerignore`. |
| Disk exhaustion | Docker, Fabric, or scanner cache fills the root disk | Check `df -h /` and `docker system df`; prune only unused images/build cache after confirming they are not needed. |
| Trivy scan | Temporary space or scanner cache issue | Check free disk and the scanner output; use a sufficiently large temporary filesystem if appropriate. |
| Git permissions | MQTT password file cannot be read or staged | The MQTT password file is a secret and must be ignored, not made public to solve a Git problem. |
| Embedded Git repository | Fabric samples appear as an embedded repository | Keep downloaded `fabric-samples/` out of this project's Git repository. |
| Git secrets | `.env` or credentials appear in staged files | Stop before commit; inspect staged filenames and ensure secrets are ignored. Rotate any secret already exposed. |

> The supplied development error log may refer to later file versions or different function names. Check the current source before applying a fix; for example, the bridge and chaincode function names must agree.

### Useful diagnostic commands

```bash
# Disk and memory
df -h /
free -h

# Docker usage
docker system df
docker ps -a

# Recent service logs
docker compose logs --tail 100
docker logs --tail 100 trade-mosquitto

# Python syntax checks
python -m compileall -q fraud_engine compliance_engine payment_vault \
  iot_logistics blockchain_ledger privacy_governance orchestrator

# Check ignored files
git check-ignore -v .env iot_logistics/mosquitto/passwd \
  blockchain_ledger/fabric-samples
```

Do not run destructive cleanup commands unless you understand which containers, images, volumes, and data they remove. Do not use broad `docker system prune --volumes` commands casually.

## Development status

This repository is a learning prototype. Before claiming a feature works, run it locally and record the actual result. The model is trained on synthetic data; its metrics do not demonstrate real-world fraud performance.

A useful evidence checklist:

- [ ] Python tests run and results recorded.
- [ ] Fraud model training output and metrics recorded.
- [ ] Compliance demonstration results recorded.
- [ ] Test-PAN-only payment demo verified; no real charge made.
- [ ] MQTT anomaly event observed.
- [ ] Fabric test-network state/history checked, if Fabric was configured.
- [ ] PII redaction and deletion demonstration checked.
- [ ] Bandit, Trivy, and ZAP reports reviewed.
- [ ] No secrets, databases, generated credentials, or confidential exam documents committed.

## Responsible use

Use synthetic or authorized test data only. Do not use the prototype to make real payment, sanctions, customs, export-control, or customer-eligibility decisions. Follow applicable laws, organizational policies, and the rules of your qualification provider.

## Licence

No licence is granted unless a licence file is added to this repository. Open-source dependencies retain their own licences. Add a project licence only if you have permission to publish the project and its contents.
README_EOF
```
