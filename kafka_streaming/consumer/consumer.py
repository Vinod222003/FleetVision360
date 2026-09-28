import json
import os

from kafka import KafkaConsumer


# Create the Bronze data directory
BRONZE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "bronze"
)

os.makedirs(BRONZE_DIR, exist_ok=True)


# Kafka topics
TOPICS = [
    "gps-events",
    "delivery-events",
    "vehicle-events"
]


# Connect to Kafka
consumer = KafkaConsumer(
    *TOPICS,
    bootstrap_servers="localhost:9092",
    group_id="fleetvision-bronze-consumer",
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda value: json.loads(value.decode("utf-8")),
)


print("==========================================")
print(" FleetVision 360 Kafka Consumer Started")
print("==========================================")
print("Listening to:")
print("  - gps-events")
print("  - delivery-events")
print("  - vehicle-events")
print()
print("Saving raw events to:")
print(BRONZE_DIR)
print()
print("Press CTRL+C to stop.")
print()


try:
    for message in consumer:

        event = message.value
        topic = message.topic

        # Create one JSON Lines file for each topic
        output_file = os.path.join(
            BRONZE_DIR,
            f"{topic}.jsonl"
        )

        # Add the Kafka metadata to the raw event
        record = {
            "kafka_topic": topic,
            "partition": message.partition,
            "offset": message.offset,
            "event": event
        }

        # Append the event to the Bronze file
        with open(output_file, "a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")

        print(f"[RECEIVED] {topic}")
        print(json.dumps(event, indent=2))
        print("-" * 50)


except KeyboardInterrupt:
    print("\nConsumer stopped.")


finally:
    consumer.close()

