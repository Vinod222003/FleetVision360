import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE_DIR = BASE_DIR / "data" / "bronze"
SILVER_DIR = BASE_DIR / "data" / "silver"

SILVER_DIR.mkdir(parents=True, exist_ok=True)


def is_valid_timestamp(value):
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


def process_file(filename, required_fields, validator):
    input_file = BRONZE_DIR / filename
    output_file = SILVER_DIR / filename

    processed = 0
    rejected = 0

    with input_file.open("r", encoding="utf-8") as infile, \
         output_file.open("w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                record = json.loads(line)
                event = record.get("event", {})

                if not all(field in event for field in required_fields):
                    rejected += 1
                    continue

                if not validator(event):
                    rejected += 1
                    continue

                silver_record = {
                    **event,
                    "_kafka_topic": record.get("kafka_topic"),
                    "_partition": record.get("partition"),
                    "_offset": record.get("offset")
                }

                outfile.write(json.dumps(silver_record) + "\n")
                processed += 1

            except (json.JSONDecodeError, TypeError):
                rejected += 1

    print(f"{filename}: {processed} processed, {rejected} rejected")


def validate_gps(event):
    return (
        isinstance(event["vehicle_id"], str)
        and is_valid_timestamp(event["timestamp"])
        and -90 <= float(event["latitude"]) <= 90
        and -180 <= float(event["longitude"]) <= 180
        and float(event["speed"]) >= 0
    )


def validate_delivery(event):
    valid_statuses = {"delayed", "picked_up", "delivered", "cancelled", "in_transit"}

    return (
        isinstance(event["order_id"], str)
        and isinstance(event["vehicle_id"], str)
        and is_valid_timestamp(event["timestamp"])
        and event["status"] in valid_statuses
        and isinstance(event["location"], str)
    )


def validate_vehicle(event):
    return (
        isinstance(event["vehicle_id"], str)
        and is_valid_timestamp(event["timestamp"])
        and event["engine_status"] in {"ON", "OFF"}
        and 0 <= float(event["fuel_level"]) <= 100
    )


process_file(
    "gps-events.jsonl",
    ["vehicle_id", "timestamp", "latitude", "longitude", "speed"],
    validate_gps
)

process_file(
    "delivery-events.jsonl",
    ["order_id", "vehicle_id", "timestamp", "status", "location"],
    validate_delivery
)

process_file(
    "vehicle-events.jsonl",
    ["vehicle_id", "timestamp", "engine_status", "fuel_level"],
    validate_vehicle
)

print("\nBronze -> Silver transformation completed.")
