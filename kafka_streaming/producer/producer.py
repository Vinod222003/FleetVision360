import json
import random
import time
from datetime import datetime, timezone

from kafka import KafkaProducer


# Connect to Kafka
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda value: json.dumps(value).encode("utf-8"),
)


VEHICLES = ["V001", "V002", "V003", "V004", "V005"]


def send_gps_event():
    vehicle_id = random.choice(VEHICLES)

    event = {
        "vehicle_id": vehicle_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latitude": round(random.uniform(12.90, 13.05), 6),
        "longitude": round(random.uniform(77.50, 77.70), 6),
        "speed": round(random.uniform(0, 80), 2),
    }

    producer.send("gps-events", value=event)

    print("GPS EVENT:", event)


def send_delivery_event():
    vehicle_id = random.choice(VEHICLES)

    event = {
        "order_id": f"ORD{random.randint(1000, 9999)}",
        "vehicle_id": vehicle_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": random.choice(
            ["picked_up", "in_transit", "delivered", "delayed"]
        ),
        "location": "Bengaluru",
    }

    producer.send("delivery-events", value=event)

    print("DELIVERY EVENT:", event)


def send_vehicle_event():
    vehicle_id = random.choice(VEHICLES)

    event = {
        "vehicle_id": vehicle_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine_status": random.choice(["ON", "OFF"]),
        "fuel_level": round(random.uniform(10, 100), 2),
    }

    producer.send("vehicle-events", value=event)

    print("VEHICLE EVENT:", event)


print("FleetVision 360 Kafka Producer Started...")
print("Sending events to Kafka...")
print("Press CTRL+C to stop.\n")


try:
    while True:

        send_gps_event()
        send_delivery_event()
        send_vehicle_event()

        producer.flush()

        time.sleep(3)

except KeyboardInterrupt:
    print("\nProducer stopped.")

finally:
    producer.close()
