import argparse
import json
import os
import random
import signal
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


def parse_args():
    parser = argparse.ArgumentParser(
        description="Publish synthetic shipment telemetry to local MQTT."
    )
    parser.add_argument("--shipment-id", default="SHIP-001")
    parser.add_argument("--interval", type=float, default=3.0)
    parser.add_argument(
        "--anomaly-every",
        type=int,
        default=5,
        help="Set 0 to disable simulated temperature breaches.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    username = os.getenv("MQTT_USERNAME", "iotdemo")
    password = os.getenv("MQTT_PASSWORD")
    if not password:
        raise SystemExit("MQTT_PASSWORD missing. Load it from .env first.")

    if args.interval <= 0:
        raise SystemExit("--interval must be greater than zero.")
    if args.anomaly_every < 0:
        raise SystemExit("--anomaly-every cannot be negative.")

    topic = f"shipments/{args.shipment_id}/telemetry"
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"sensor-{args.shipment_id}",
        protocol=mqtt.MQTTv311,
    )
    client.username_pw_set(username, password)
    client.connect("127.0.0.1", 1883, keepalive=30)
    client.loop_start()

    running = True

    def stop(_signum, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    sequence = 0
    print(f"Publishing synthetic data to {topic}; Ctrl+C to stop.")

    try:
        while running:
            sequence += 1
            breach = (
                args.anomaly_every > 0
                and sequence % args.anomaly_every == 0
            )

            event = {
                "event_id": f"{args.shipment_id}-{sequence:06d}",
                "shipment_id": args.shipment_id,
                "sequence": sequence,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "location": {
                    "lat": round(25.2048 + random.uniform(-0.02, 0.02), 6),
                    "lon": round(55.2708 + random.uniform(-0.02, 0.02), 6),
                    "label": "Dubai Port (simulated)",
                },
                "temp_c": round(12.0 if breach else random.uniform(3.0, 7.5), 2),
                "humidity_pct": round(random.uniform(35.0, 65.0), 1),
                "seal_tampered": False,
            }

            result = client.publish(topic, json.dumps(event), qos=1)
            result.wait_for_publish(timeout=5)

            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"⚠️ Publish failed: rc={result.rc}")
            else:
                print(
                    f"Published event={event['event_id']} "
                    f"temp={event['temp_c']}C breach={breach}"
                )

            time.sleep(args.interval)
    finally:
        client.loop_stop()
        client.disconnect()
        print("Sensor simulator stopped.")


if __name__ == "__main__":
    main()
