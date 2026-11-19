# 🐛 Errors Faced & Resolved — Global Trade Platform

> Complete troubleshooting log for the Global Trade Platform project.  
> **Total issues:** 30+ · **Categories:** 9 · **Stack:** Python · FastAPI · Docker · Hyperledger Fabric · Mosquitto · Trivy

---

## 📑 Table of Contents

1. [Heredoc / Paste Corruption](#-category-1-heredoc--paste-corruption)
2. [MQTT / Mosquitto](#-category-2-mqtt--mosquitto)
3. [Python Environment](#-category-3-python-environment)
4. [Hyperledger Fabric](#-category-4-hyperledger-fabric)
5. [Bridge / Orchestrator](#-category-5-bridge--orchestrator)
6. [Docker / Compose](#-category-6-docker--compose)
7. [Disk / Trivy / Security](#-category-7-disk--trivy--security)
8. [Git](#-category-8-git)
9. [Testing (Pytest)](#-category-9-testing-pytest)
10. [Summary & Runbook](#-summary--daily-startup-runbook)

---

## 📦 Category 1: Heredoc / Paste Corruption

> **Pattern:** `cat <<'EOF' > file` mein `EOF` terminator unique nahi tha, isliye aage ki commands file mein ghus gayi. Yeh **5+ baar** hua.

| # | Error | Cause | Fix |
|---|---|---|---|
| 1.1 | `shipment.go` mein `EOF     }       panic(...))ntry: %w", err)` jaisi lines aa gayin | `EOF` ne heredoc terminate nahi kiya | Unique terminator use karein: `GOEOF`, `PYEOF`, `YAMLEOF`, `GITEOF` — plain `EOF` **kabhi nahi** |
| 1.2 | `bridge_api.py` mein `python -m compileall ...` line ghus gayi | Same reason | `PYEOF` use karein ya `nano`/`vim` se directly likhein |
| 1.3 | `Dockerfile` mein `["uvicorn", ...]` heredoc ke bahar reh gaya → `CMD` missing | Heredoc premature terminate | `nano Dockerfile` se seedha add karein |
| 1.4 | `.github/workflows/devsecops.yml` mein `exit-code: "1"H,CRITICAL"sconfig"8.0...` ghus gaya | Heredoc corruption | `YAMLEOF` se clean rewrite + YAML validate |
| 1.5 | `.gitignore` end mein `GITEOF.db` aa gaya | Heredoc corruption | `GITEOF` se rewrite |

**Fix for 1.3:**
```dockerfile
CMD ["uvicorn", "orchestrator.checkout_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Verification after every heredoc:**
```bash
grep -nE '^YOUR_TERMINATOR' <file>   # khaali hona chahiye
tail -3 <file>                        # sahi ending
file <file>                           # "ASCII text" ya "UTF-8"
```

**Verify YAML specifically:**
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/devsecops.yml')); print('YAML OK')"
```

---

## 📦 Category 2: MQTT / Mosquitto

| # | Error | Cause | Fix |
|---|---|---|---|
| 2.1 | `mount src=.../iot_logistics/iot_logistics/...` — `not a directory` | Compose file `iot_logistics/` mein thi, paths `./iot_logistics/...` likhe the → double ho gaya | Volume paths ko compose file se relative karein: `./mosquitto/mosquitto.conf` |
| 2.2 | `password-file: Error: Unable to open pwfile` — infinite restart loop | `mosquitto_passwd` ne file `root:root 600` banayi, Mosquitto `1883:1883` pe chalta hai | `sudo chown 1883:1883 mosquitto/passwd && sudo chmod 600` + same for `data/` `log/` |
| 2.3 | `read -rsp "[REDACTED]" MQTT_PASSWORD` — password capture nahi hua | `-p` ke baad **prompt** aata hai, password nahi | `read -rsp "MQTT password: " MQTT_PASSWORD` (prompt plain text) |
| 2.4 | `.env` mein `MQTT_PASSWORD=` (empty) save hua | Upar wali galti ka result | Line delete karein: `grep -v '^MQTT_PASSWORD=' .env > .env.tmp && mv .env.tmp .env`, phir sahi se add |
| 2.5 | `mqtt_listener.py`: `MQTT_PASSWORD missing. Load it from .env first.` | `.env` source nahi kiya | `set -a; source .env; set +a` phir `python iot_logistics/mqtt_listener.py` |
| 2.6 | `ConnectionRefusedError: [Errno 111] Connection refused` on `127.0.0.1:1883` | Mosquitto container down | `docker compose -f iot_logistics/mosquitto.compose.yml up -d` + logs check |

**Fix for 2.2 (full block):**
```bash
docker run --rm -it \
  -v "$PWD/iot_logistics/mosquitto:/mosquitto/config" \
  eclipse-mosquitto:2 \
  mosquitto_passwd -c /mosquitto/config/passwd iotdemo

sudo chown 1883:1883 iot_logistics/mosquitto/passwd
sudo chmod 600 iot_logistics/mosquitto/passwd
sudo chown -R 1883:1883 iot_logistics/mosquitto/data iot_logistics/mosquitto/log

docker compose -f iot_logistics/mosquitto.compose.yml restart
sleep 2
docker logs --tail 10 trade-mosquitto
```

---

## 📦 Category 3: Python Environment

| # | Error | Cause | Fix |
|---|---|---|---|
| 3.1 | `Command 'python' not found` | Ubuntu 24.04 sirf `python3` deta hai | `sudo apt install python-is-python3` **ya** har jagah `python3` use karein |
| 3.2 | `ModuleNotFoundError: No module named 'fastapi'` | System `uvicorn` (apt) install kiya lekin venv activate nahi hua + fastapi missing | `source venv/bin/activate && pip install fastapi "uvicorn[standard]" pydantic` |
| 3.3 | `pytest ModuleNotFoundError: No module named 'privacy_governance'` | pytest project root ko `sys.path` mein nahi daalta | `pytest.ini` banayein (neeche dekhein) |

**Fix for 3.1:**
```bash
sudo apt install -y python-is-python3
python --version   # verify
```

**Fix for 3.2:**
```bash
cd ~/global-trade-platform
source venv/bin/activate
pip install fastapi "uvicorn[standard]" pydantic
python -c "import fastapi, uvicorn, pydantic; print('OK')"
```

**Fix for 3.3 — `pytest.ini`:**
```ini
[pytest]
pythonpath = .
testpaths = tests
filterwarnings =
    ignore::DeprecationWarning:spacy.*
```

---

## 📦 Category 4: Hyperledger Fabric

| # | Error | Cause | Fix |
|---|---|---|---|
| 4.1 | `fabric-samples/test-network/network.sh: No such file` | `install-fabric.sh docker binary` — `samples` argument nahi diya | `./install-fabric.sh docker binary samples` |
| 4.2 | `"go": executable file not found in $PATH` (chaincode package fail) | Go compiler install nahi tha | `sudo apt install golang-go` + `go version` se verify |
| 4.3 | `go: missing go.sum entry for module...` | `go.sum` generate nahi hua | `cd chaincode/shipment && go mod tidy` |
| 4.4 | `string field contains invalid UTF-8` (chaincode install) | Corrupt source file (`shipment.go` mein garbage lines) | Clean rewrite with `GOEOF` terminator, `go build ./...` se verify |
| 4.5 | `Function ReadShipment not found` | `bridge_api.py` mein galat function name | `sed -i 's/ReadShipment/QueryShipment/g' blockchain_ledger/bridge_api.py blockchain_ledger/fabric_cli.sh` |
| 4.6 | `ENDORSEMENT_POLICY_FAILURE` | `fabric_cli.sh` mein sirf ek `--peerAddresses` (org1), policy `MAJORITY` hai (dono chahiye) | `nano fabric_cli.sh` → org2 add karein |
| 4.7 | `peer: command not found` (manual test) | `fabric-samples/bin` PATH mein nahi | `export PATH=$PWD/../bin:$PATH` (test-network dir mein) |
| 4.8 | `Orderer TLS certificate not found: .../orderers/orderer.example.com/msp/tlscacerts/...` | Galat path — actual path `ordererOrganizations/example.com/tlsca/` hai | `fabric_cli.sh` mein `ORDERER_CA` line edit karein |
| 4.9 | Saare certs missing (`organizations/` khaali) | `network.sh down` chalaya tha → containers + crypto + volumes delete | `./network.sh up createChannel` + `./network.sh deployCC` |
| 4.10 | `AddEvent` / `GetShipmentHistory` function missing | Chaincode v1.0 mein sirf `CreateShipment`/`QueryShipment` the | `shipment.go` mein dono functions add + `deployCC -ccv 1.1 -ccs auto` |
| 4.11 | `shipment SHIP-001 already exists` | Idempotent create — same ID dobara bhej diya | Har test ke liye naya `order_id`/`shipment_id` use karein |

**Fix for 4.6 — `fabric_cli.sh` mein org2 add:**

Yeh line pehle:
```bash
--peerAddresses localhost:7051 \
--tlsRootCertFiles "$CORE_PEER_TLS_ROOTCERT_FILE" \
```

Iske baad add karein:
```bash
--peerAddresses localhost:9051 \
--tlsRootCertFiles "$PEER0_ORG2_TLS" \
```

Aur upar variable define karein:
```bash
PEER0_ORG2_TLS="${TEST_NETWORK}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
```

**Fix for 4.8 — correct `ORDERER_CA`:**
```bash
ORDERER_CA="${TEST_NETWORK}/organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem"
```

**Fix for 4.9 + 4.10 — full network recreate:**
```bash
cd ~/global-trade-platform/blockchain_ledger/fabric-samples/test-network
./network.sh down
./network.sh up createChannel -c supplychain -ca
./network.sh deployCC \
  -c supplychain \
  -ccn shipment \
  -ccp ../chaincode/shipment \
  -ccl go \
  -ccv 1.1 \
  -ccs auto
```

**Verify certs exist:**
```bash
for f in \
  organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem \
  organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
  organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt \
  ../bin/peer
do
  [ -f "$f" ] && echo "✅ $f" || echo "❌ MISSING: $f"
done
```

---

## 📦 Category 5: Bridge / Orchestrator

| # | Error | Cause | Fix |
|---|---|---|---|
| 5.1 | `fabric_cli.sh` not found | `bridge_api.py` reference karta hai lekin file exist nahi karti thi | Script create karein (neeche) |
| 5.2 | Bridge `POST /api/v1/shipments` → **502 Bad Gateway** | (a) path/action mismatch, (b) TLS path galat, (c) sirf ek peer | 4.5, 4.6, 4.8 dekhein |
| 5.3 | Checkout response `.shipment: null` | Response `DEMO_ORDER_ACCEPTED` tak nahi pahuncha (BLOCKED/STEP_UP/error) | **`jq` hata kar raw JSON dekhein** — `checkout_status` padhein |
| 5.4 | `country code 'GB' has no configured demo region` | `region_store.py` mein GB mapping nahi | `customer_country`, `ip_country`, `card_country`, `destination_country` — chaaron `DE` karein |
| 5.5 | `FABRIC_BRIDGE_URL` container se `127.0.0.1` reach nahi | Container ke andar `127.0.0.1` = container khud | `extra_hosts` + `host.docker.internal` |
| 5.6 | Orchestrator startup pe `FABRIC_BRIDGE_URL` empty | `load_dotenv()` sirf startup pe padhta hai | Restart karein `set -a; source .env; set +a` ke saath |
| 5.7 | `Port 8000 already in use` (compose bind fail) | Manual uvicorn chal raha tha | `lsof -ti:8000 \| xargs -r kill` |

**Fix for 5.1 — `fabric_cli.sh`:**
```bash
#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:?Expected action: invoke or query}"
PAYLOAD="${2:?Expected JSON chaincode payload}"

FABRIC_DIR="${HOME}/global-trade-platform/blockchain_ledger/fabric-samples"
TEST_NETWORK="${FABRIC_DIR}/test-network"

cd "$TEST_NETWORK"

export PATH="${FABRIC_DIR}/bin:${PATH}"
export FABRIC_CFG_PATH="${FABRIC_DIR}/config"
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_MSPCONFIGPATH="${TEST_NETWORK}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp"
export CORE_PEER_ADDRESS="localhost:7051"
export CORE_PEER_TLS_ROOTCERT_FILE="${TEST_NETWORK}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"

ORDERER_CA="${TEST_NETWORK}/organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem"
PEER0_ORG2_TLS="${TEST_NETWORK}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"

if [[ "$ACTION" == "invoke" ]]; then
  exec peer chaincode invoke \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --tls \
    --cafile "$ORDERER_CA" \
    -C supplychain \
    -n shipment \
    --peerAddresses localhost:7051 \
    --tlsRootCertFiles "$CORE_PEER_TLS_ROOTCERT_FILE" \
    --peerAddresses localhost:9051 \
    --tlsRootCertFiles "$PEER0_ORG2_TLS" \
    -c "$PAYLOAD" \
    --waitForEvent
elif [[ "$ACTION" == "query" ]]; then
  exec peer chaincode query \
    -C supplychain \
    -n shipment \
    -c "$PAYLOAD"
else
  echo "Unsupported action: $ACTION" >&2
  exit 2
fi
```

**Fix for 5.5 — `docker-compose.yml`:**
```yaml
services:
  app:
    # ...
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

Aur `.env`:
```bash
FABRIC_BRIDGE_URL=http://host.docker.internal:8004
```

---

## 📦 Category 6: Docker / Compose

| # | Error | Cause | Fix |
|---|---|---|---|
| 6.1 | `failed to bind host port 127.0.0.1:8000/tcp: address already in use` | Manual process port hold kar raha tha | `lsof -ti:8000 \| xargs -r kill` |
| 6.2 | `Dockerfile` missing `CMD` | Paste corruption ne `CMD` line bahar nikaal di | `nano Dockerfile` → `CMD ["uvicorn", ...]` |
| 6.3 | Build context **719 MB** | `.dockerignore` mein `fabric-samples/`, `venv/`, `*.sqlite` missing | `.dockerignore` extend karein |

**Fix for 6.3 — `.dockerignore`:**
```dockerignore
.env
venv/
.git/
__pycache__/
*.pyc
*.db
*.sqlite3
*.log
reports/
logs/
blockchain_ledger/fabric-samples/
blockchain_ledger/*.tar.gz
**/vendor/
tests/
```

---

## 📦 Category 7: Disk / Trivy / Security

| # | Error | Cause | Fix |
|---|---|---|---|
| 7.1 | `Trivy: remote Maven repository returned 429 Too Many Requests` | Trivy `pom.xml` parent POMs remote se resolve kar raha tha | `--offline-scan` flag (Python project hai) |
| 7.2 | `Trivy: write /tmp/trivy-.../cached-file: no space left on device` | Disk 94% full — `/tmp` root fs pe | `TMPDIR=/var/tmp trivy image ...` |
| 7.3 | Disk 25 GB jaldi bhar gaya | `/var/lib/containerd` = **13 GB** | `docker builder prune -af` + `docker image prune -f` + `docker system prune -af` |
| 7.4 | Bandit `B310: Audit url open` (Medium) | `urllib.request.urlopen` `file://` scheme accept karta hai | `httpx.post()` se replace karein |

**Fix for 7.1 + 7.2 — combined Trivy command:**
```bash
TMPDIR=/var/tmp trivy fs \
  --offline-scan \
  --scanners vuln,secret,misconfig \
  --severity HIGH,CRITICAL \
  --exit-code 1 \
  --skip-dirs "venv,blockchain_ledger/fabric-samples" \
  .
```

**Fix for 7.3 — disk cleanup:**
```bash
docker builder prune -af
docker image prune -f
docker container prune -f
pip cache purge
rm -rf ~/.cache/trivy
sudo journalctl --vacuum-size=200M
sudo apt-get clean
df -h /
```

**Fix for 7.4 — `iot_logistics/mqtt_listener.py`:**

`urllib` ko `httpx` se replace karein:
```python
import httpx

try:
    response = httpx.post(
        f"{BRIDGE_URL}/api/v1/shipments",
        json=payload,
        timeout=65,
    )
    response.raise_for_status()
except httpx.HTTPError as exc:
    logger.error("Bridge call failed: %s", exc)
```

**Permanent cron — `sudo crontab -e`:**
```cron
# Har Sunday 3 AM — Docker cleanup
0 3 * * 0 /usr/bin/docker builder prune -af > /dev/null 2>&1
0 3 * * 0 /usr/bin/docker image prune -f > /dev/null 2>&1
0 3 * * 0 /usr/bin/journalctl --vacuum-size=200M > /dev/null 2>&1
```

---

## 📦 Category 8: Git

| # | Error | Cause | Fix |
|---|---|---|---|
| 8.1 | `fatal: not a git repository` | `git init` nahi kiya tha | `git init && git config user.email ... && git config user.name ...` |
| 8.2 | `error: open("iot_logistics/mosquitto/passwd"): Permission denied` | File `1883:1883 600` — ubuntu user read nahi kar sakta | `.gitignore` mein add: `iot_logistics/mosquitto/passwd` (aur `acl`) |
| 8.3 | `warning: adding embedded git repository: blockchain_ledger/fabric-samples` | `fabric-samples` apna `.git` rakhta hai | `.gitignore` mein `blockchain_ledger/fabric-samples/` add |
| 8.4 | `.env` galti se commit hone ka risk | `.gitignore` mein `.env` tha lekin verify nahi kiya | `git check-ignore -v .env` se verify |

**Fix for 8.2, 8.3 — `.gitignore` (complete):**
```gitignore
# === Secrets ===
.env
.env.*
!.env.example
iot_logistics/mosquitto/passwd
iot_logistics/mosquitto/acl

# === Python ===
venv/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.coverage
htmlcov/

# === Data / DB ===
*.sqlite
*.sqlite3
*.db
privacy_governance/data/
payment_vault/data/
iot_logistics/data/
iot_logistics/mosquitto/data/
iot_logistics/mosquitto/log/
fraud_engine/data/
fraud_engine/models/
compliance_engine/customs_docs/

# === Fabric (regenerated) ===
blockchain_ledger/fabric-samples/
blockchain_ledger/*.tar.gz
blockchain_ledger/bin/
blockchain_ledger/config/
**/organizations/
**/system-genesis-block/
**/channel-artifacts/

# === Reports / logs ===
reports/
logs/
*.log

# === OS ===
.DS_Store
Thumbs.db
```

**Safe commit workflow:**
```bash
cd ~/global-trade-platform
git check-ignore -v .env iot_logistics/mosquitto/passwd blockchain_ledger/fabric-samples
# Teeno non-empty output hona chahiye

git add -A
git diff --cached --name-only | grep -E '\.env$|passwd|acl' && echo "⚠️ STOP" || echo "✅ Clean"
git commit -m "message"
```

---

## 📦 Category 9: Testing (Pytest)

| # | Error | Fix |
|---|---|---|
| 9.1 | `ModuleNotFoundError: No module named 'privacy_governance'` | `pytest.ini` with `pythonpath = .` |
| 9.2 | spaCy `DeprecationWarning: Importing 'parser.split_arg_string'` | Ignore (spaCy/Click internal) **ya** `filterwarnings` in `pytest.ini` |
| 9.3 | `1 passed, 2 warnings` | Warnings noise hai, no action needed |

**Final `pytest.ini`:**
```ini
[pytest]
pythonpath = .
testpaths = tests
filterwarnings =
    ignore::DeprecationWarning:spacy.*
    ignore::PendingDeprecationWarning:starlette.*
```

---

## 🎯 Summary — Top Recurring Patterns

| Pattern | Baar aaya | Root fix |
|---|---|---|
| **Heredoc corruption** | 5+ baar | Unique terminators (`PYEOF`, `GOEOF`, etc.) + `nano` for critical files |
| **Path doubling / wrong paths** | 3 baar | Compose paths relative to compose file; Fabric certs actual path verify |
| **Permissions (`root` vs `1883`)** | 3 baar | `mosquitto_passwd` ke baad `chown 1883:1883` |
| **`source .env` bhoolna** | 3 baar | `set -a; source .env; set +a` habit banayein |
| **`python` vs `python3`** | 3 baar | `apt install python-is-python3` ya venv hamesha activate |
| **Sirf ek `--peerAddresses`** | 1 baar (bada) | Dono orgs ka endorsement chahiye (`MAJORITY` policy) |
| **Disk full** | 1 baar | `docker builder prune -af` weekly + `.dockerignore` |

---

## 📋 Daily Startup Runbook

Aapka stack down hone par **is order mein** start karein:

### Step 1 — Fabric Network (5 min)

```bash
cd ~/global-trade-platform/blockchain_ledger/fabric-samples/test-network
./network.sh up createChannel -c supplychain -ca
./network.sh deployCC \
  -c supplychain \
  -ccn shipment \
  -ccp ../chaincode/shipment \
  -ccl go \
  -ccv 1.1 \
  -ccs auto

# Verify
docker ps --format '{{.Names}}' | grep -E "peer|orderer"
# Expected: 3-4 containers
```

### Step 2 — Bridge (Terminal 2)

```bash
cd ~/global-trade-platform && source venv/bin/activate
uvicorn blockchain_ledger.bridge_api:app --host 127.0.0.1 --port 8004

# Verify (from another terminal)
curl -s http://127.0.0.1:8004/health
# Expected: {"status":"ok",...}
```

### Step 3 — Mosquitto (Terminal 3)

```bash
cd ~/global-trade-platform
docker compose -f iot_logistics/mosquitto.compose.yml up -d

# Verify
docker ps --filter name=trade-mosquitto --format '{{.Status}}'
# Expected: Up (no "Restarting")
```

### Step 4 — Orchestrator (Terminal 4)

```bash
cd ~/global-trade-platform && source venv/bin/activate
set -a; source .env; set +a
uvicorn orchestrator.checkout_api:app --host 127.0.0.1 --port 8000

# Verify
curl -s http://127.0.0.1:8000/health
```

### Step 5 — MQTT Listener (Terminal 5)

```bash
cd ~/global-trade-platform && source venv/bin/activate
set -a; source .env; set +a
python iot_logistics/mqtt_listener.py

# Expected: "✅ Connected to local MQTT broker."
```

---

## 🚨 Pre-Commit Checklist

Before every `git commit`:

- [ ] `git check-ignore -v .env` → non-empty output
- [ ] `git check-ignore -v iot_logistics/mosquitto/passwd` → non-empty
- [ ] `git check-ignore -v blockchain_ledger/fabric-samples` → non-empty
- [ ] `git diff --cached --name-only | grep -E '\.env$|passwd|acl|\.sqlite'` → empty
- [ ] `pytest -q` → all green
- [ ] `bandit -r ... -ll` → no Medium/High
- [ ] `df -h /` → > 20% free

---

## 🛠 Quick Diagnostic Commands

### Stack health check (all at once)

```bash
echo "=== Fabric ===" && docker ps --format '{{.Names}}' | grep -E "peer|orderer" | wc -l
echo "=== Bridge ===" && curl -s --max-time 2 http://127.0.0.1:8004/health || echo "DOWN"
echo "=== Mosquitto ===" && docker ps --filter name=trade-mosquitto --format '{{.Status}}'
echo "=== Orchestrator ===" && curl -s --max-time 2 http://127.0.0.1:8000/health || echo "DOWN"
echo "=== Disk ===" && df -h / | tail -1
```

### Port check

```bash
ss -tlnp | grep -E ':(1883|8000|8004|7050|7051|9051)'
```

### Process check

```bash
pgrep -af "uvicorn|mqtt_listener" | grep -v grep
```

---

## 📚 Reference Links

- [Hyperledger Fabric Docs](https://hyperledger-fabric.readthedocs.io/)
- [Mosquitto Configuration](https://mosquitto.org/man/mosquitto-conf-5.html)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Trivy Docs](https://trivy.dev/latest/docs/)
- [Bandit Rules](https://bandit.readthedocs.io/en/latest/plugins/index.html)

---

**Document Version:** 1.0  
**Last Updated:** 2026-11-17  
**Maintainer:** Saad Khan  
**Status:** ✅ All issues resolved & tested

---

> 💡 **Golden Rule:** Heredoc terminators always unique. Files critical → `nano`. Every paste → verify. Every deploy → health check.
