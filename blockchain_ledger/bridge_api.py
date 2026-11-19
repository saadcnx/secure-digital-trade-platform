import json
import subprocess
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
CLI = BASE_DIR / "fabric_cli.sh"

app = FastAPI(
    title="Local Shipment Ledger Bridge",
    version="1.0.0",
    description="Educational local bridge to the Hyperledger Fabric test network.",
)


class CreateShipmentRequest(BaseModel):
    shipment_id: str = Field(min_length=1, max_length=64)
    origin: str = Field(min_length=2, max_length=80)
    destination: str = Field(min_length=2, max_length=80)
    custodian: str = Field(min_length=2, max_length=100)


class ShipmentEventRequest(BaseModel):
    status: str = Field(min_length=2, max_length=64)
    location: str = Field(min_length=2, max_length=120)
    custodian: str = Field(min_length=2, max_length=100)
    temperature_c: float = Field(ge=-80, le=100)
    seal_tampered: bool = False


def run_fabric(action: str, payload: dict[str, Any]) -> str:
    if not CLI.exists():
        raise HTTPException(status_code=500, detail="Fabric CLI helper not found")

    try:
        result = subprocess.run(
            [str(CLI), action, json.dumps(payload, separators=(",", ":"))],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Fabric command timed out") from exc

    if result.returncode != 0:
        # Return a bounded diagnostic, not environment variables or secrets.
        diagnostic = (result.stderr or result.stdout)[-3000:]
        raise HTTPException(
            status_code=502,
            detail={"message": "Fabric command failed", "diagnostic": diagnostic},
        )

    return result.stdout.strip()


@app.get("/health")
def health():
    return {"status": "healthy", "service": "local_fabric_bridge"}


@app.post("/api/v1/shipments")
def create_shipment(request: CreateShipmentRequest):
    payload = {
        "function": "CreateShipment",
        "Args": [
            request.shipment_id,
            request.origin,
            request.destination,
            request.custodian,
        ],
    }
    output = run_fabric("invoke", payload)
    return {
        "result": "shipment_create_submitted",
        "shipment_id": request.shipment_id,
        "fabric_output": output,
    }


@app.post("/api/v1/shipments/{shipment_id}/events")
def update_shipment(shipment_id: str, request: ShipmentEventRequest):
    payload = {
        "function": "UpdateShipment",
        "Args": [
            shipment_id,
            request.status,
            request.location,
            request.custodian,
            str(request.temperature_c),
            str(request.seal_tampered).lower(),
        ],
    }
    output = run_fabric("invoke", payload)
    return {
        "result": "shipment_update_submitted",
        "shipment_id": shipment_id,
        "fabric_output": output,
    }


@app.get("/api/v1/shipments/{shipment_id}")
def read_shipment(shipment_id: str):
    payload = {"function": "QueryShipment", "Args": [shipment_id]}
    output = run_fabric("query", payload)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"fabric_output": output}


@app.get("/api/v1/shipments/{shipment_id}/history")
def shipment_history(shipment_id: str):
    payload = {"function": "GetShipmentHistory", "Args": [shipment_id]}
    output = run_fabric("query", payload)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"fabric_output": output}
