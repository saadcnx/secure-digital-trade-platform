import hashlib
import json
import os
import signal
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt


BASE_DIR = Path(__file__).resolve().parent
EVENTS_FILE = BASE_DIR / "data" / "telemetry_events.jsonl"
TEMP_LIMIT_C = float(os.getenv("COLD_CHAIN_LIMIT_C", "8.0"))
LEDGER_URL = os.getenv(
    "LEDGER_API_URL",
    "http://127.0.0.1:8004/api/v1/shipments",
)


def submit_ledger_update(shipment_id: str, event: dict, flags: list[str]) -> None:
    status = (
        "COMPROMISED_COLD_CHAIN"
        if "COLD_CHAIN_TEMPERATURE_BREACH" in flags
        else "SEAL_TAMPERED"
        if "SHIPMENT_SEAL_TAMPERED" in flags
        else "IN_TRANSIT"
    )

    payload = {
        "status": status,
        "location": str(event.get("location", {}).get("label", "UNKNOWN")),
        "custodian": "LogisticsSensor",
        "temperature_c": float(event["temp_c"]),
        "seal_tampered": bool(event.get("seal_tampered", False)),
    }

    request = urllib.request.Request(
        f"{LEDGER_URL}/{shipment_id}/events",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=65) as response:
            response.read()
        print(f"⛓️ Ledger updated: {shipment_id} -> {status}")
    except (urllib.error.URLError, TimeoutError) as exc:
        # The local JSONL event remains saved; an operator can retry later.
        print(f"⚠️ Ledger update failed; event was saved locally: {exc}")


def main():
    username = os.getenv("MQTT_USERNAME", "iotdemo")
    password = os.getenv("MQTT_PASSWORD")
    if not password:
        raise SystemExit("MQTT_PASSWORD missing. Load it from .env first.")

    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    running = True

    def stop(_signum, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print("✅ Connected to local MQTT broker.")
            client.subscribe("shipments/+/telemetry", qos=1)
        else:
            print(f"❌ MQTT connection failed: {reason_code}")

    def on_message(client, userdata, message):
        try:
            event = json.loads(message.payload.decode("utf-8"))
            shipment_id = str(event["shipment_id"])
            temp_c = float(event["temp_c"])
            seal_tampered = bool(event.get("seal_tampered", False))

            if not shipment_id or len(shipment_id) > 64:
                raise ValueError("Invalid shipment_id")

            flags = []
            if temp_c > TEMP_LIMIT_C:
                flags.append("COLD_CHAIN_TEMPERATURE_BREACH")
            if seal_tampered:
                flags.append("SHIPMENT_SEAL_TAMPERED")

            record = {
                "received_at": datetime.now(timezone.utc).isoformat(),
                "topic": message.topic,
                "event": event,
                "anomaly": bool(flags),
                "flags": flags,
            }

            canonical = json.dumps(record, sort_keys=True).encode("utf-8")
            record["event_sha256"] = hashlib.sha256(canonical).hexdigest()

            with EVENTS_FILE.open("a", encoding="utf-8") as file:
                file.write(json.dumps(record) + "\n")

            if flags:
                print(
                    f"🚨 ANOMALY shipment={shipment_id} "
                    f"temp={temp_c}C flags={flags}"
                )
                submit_ledger_update(shipment_id, event, flags)
            else:
                print(f"✅ Normal telemetry shipment={shipment_id} temp={temp_c}C")

        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            print(f"⚠️ Invalid telemetry message ignored: {exc}")

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="trade-telemetry-listener",
        protocol=mqtt.MQTTv311,
    )
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("127.0.0.1", 1883, keepalive=30)

    try:
        client.loop_start()
        while running:
            time.sleep(0.5)
    finally:
        client.loop_stop()
        client.disconnect()
        print("MQTT listener stopped.")


if __name__ == "__main__":
    main()
