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


# Create 100 vehicles around Bengaluru
vehicles = []

base_latitude = 12.9716
base_longitude = 77.5946

for i in range(1, 101):

    row = (i - 1) // 10
    column = (i - 1) % 10

    vehicles.append({
        "vehicle_id": f"V{i:03d}",
        "latitude": base_latitude + (row * 0.01),
        "longitude": base_longitude + (column * 0.01),
        "speed": 40 + (i % 40),
    })


def send_gps_events():
    """Send GPS data for all 100 vehicles."""

    for vehicle in vehicles:

        event = {
            "vehicle_id": vehicle["vehicle_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": round(vehicle["latitude"], 6),
            "longitude": round(vehicle["longitude"], 6),
            "speed": vehicle["speed"],
        }

        producer.send("gps-events", value=event)

        # Move vehicle slightly for the next update
        vehicle["latitude"] += 0.0001
        vehicle["longitude"] += 0.0001

        print("GPS EVENT:", event)


def send_delivery_event():
    """Send a simulated delivery event."""

    vehicle = random.choice(vehicles)

    event = {
        "order_id": f"ORD{random.randint(1000, 9999)}",
        "vehicle_id": vehicle["vehicle_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": random.choice(
            ["picked_up", "in_transit", "delivered", "delayed"]
        ),
        "location": "Bengaluru",
    }

    producer.send("delivery-events", value=event)

    print("DELIVERY EVENT:", event)


def send_vehicle_event():
    """Send a simulated vehicle status event."""

    vehicle = random.choice(vehicles)

    event = {
        "vehicle_id": vehicle["vehicle_id"],
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

        # Send GPS data for all 100 vehicles
        send_gps_events()

        # Keep original delivery and vehicle events
        send_delivery_event()
        send_vehicle_event()

        producer.flush()

        print("==========================================")
        print("Sent GPS data for 100 vehicles")
        print("Sent delivery event")
        print("Sent vehicle event")
        print("==========================================")

        time.sleep(5)

except KeyboardInterrupt:
    print("\nProducer stopped.")

finally:
    producer.close()