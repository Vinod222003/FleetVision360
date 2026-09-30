import json
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
)

# Project folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Bronze input
BRONZE_FILE = BASE_DIR / "data" / "bronze" / "gps-events.jsonl"

# Silver output
SILVER_DIR = BASE_DIR / "data" / "silver" / "gps"
SILVER_FILE = SILVER_DIR / "gps_data.jsonl"


# Start Spark
spark = (
    SparkSession.builder
    .appName("FleetVision360-BronzeToSilver")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# --------------------------------------------------
# 1. Read Bronze data using Python
# --------------------------------------------------

records = []

with open(BRONZE_FILE, "r", encoding="utf-8") as file:
    for line in file:
        if line.strip():
            records.append(json.loads(line))

print(f"Bronze records found: {len(records)}")


# --------------------------------------------------
# 2. Extract GPS event
# --------------------------------------------------

gps_records = []

for record in records:

    event = record["event"]

    gps_records.append({
        "vehicle_id": event["vehicle_id"],
        "timestamp": event["timestamp"],
        "latitude": float(event["latitude"]),
        "longitude": float(event["longitude"]),
        "speed": float(event["speed"]),
    })


# --------------------------------------------------
# 3. Create PySpark DataFrame
# --------------------------------------------------

schema = StructType([
    StructField("vehicle_id", StringType(), False),
    StructField("timestamp", StringType(), False),
    StructField("latitude", DoubleType(), False),
    StructField("longitude", DoubleType(), False),
    StructField("speed", DoubleType(), False),
])

df = spark.createDataFrame(
    gps_records,
    schema=schema
)


# --------------------------------------------------
# 4. PySpark transformations
# --------------------------------------------------

# Remove duplicate GPS events
df = df.dropDuplicates([
    "vehicle_id",
    "timestamp"
])

# Sort data
df = df.orderBy(
    "vehicle_id",
    "timestamp"
)


print("\nSilver GPS data:")
df.show(10, truncate=False)


# --------------------------------------------------
# 5. Collect processed data
# --------------------------------------------------

processed_records = df.collect()


# --------------------------------------------------
# 6. Write Silver file using normal Python
# --------------------------------------------------

SILVER_DIR.mkdir(parents=True, exist_ok=True)

with open(SILVER_FILE, "w", encoding="utf-8") as file:

    for row in processed_records:

        record = {
            "vehicle_id": row["vehicle_id"],
            "timestamp": row["timestamp"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "speed": row["speed"],
        }

        file.write(json.dumps(record) + "\n")


# --------------------------------------------------
# 7. Finish
# --------------------------------------------------

print()
print("==========================================")
print(" Bronze -> Silver processing completed")
print("==========================================")

print(f"Silver records: {len(processed_records)}")
print(f"Silver output: {SILVER_FILE}")

spark.stop()