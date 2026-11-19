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

if [[ ! -x "${FABRIC_DIR}/bin/peer" ]]; then
  echo "Fabric peer CLI not found: ${FABRIC_DIR}/bin/peer" >&2
  exit 2
fi

if [[ ! -f "$ORDERER_CA" ]]; then
  echo "Orderer TLS certificate not found: $ORDERER_CA" >&2
  exit 2
fi

if [[ ! -f "$PEER0_ORG2_TLS" ]]; then
  echo "Org2 peer TLS certificate not found: $PEER0_ORG2_TLS" >&2
  exit 2
fi

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
