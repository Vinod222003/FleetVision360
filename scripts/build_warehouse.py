import csv
import sqlite3
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
DB_DIR = BASE / "data" / "warehouse"

DB_DIR.mkdir(parents=True, exist_ok=True)

DB = DB_DIR / "fleetvision360.db"

# Remove old database so we build it cleanly
if DB.exists():
    DB.unlink()

conn = sqlite3.connect(DB)
cur = conn.cursor()

# ============================================================
# CREATE TABLES
# ============================================================

cur.executescript("""
CREATE TABLE dim_depot (
    depot_key INTEGER PRIMARY KEY AUTOINCREMENT,
    depot_id TEXT UNIQUE NOT NULL,
    depot_name TEXT,
    city TEXT,
    capacity INTEGER
);

CREATE TABLE dim_vehicle (
    vehicle_key INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id TEXT UNIQUE NOT NULL,
    type TEXT,
    depot_id TEXT,
    capacity INTEGER,
    model TEXT,
    fuel_capacity_liters REAL
);

CREATE TABLE dim_driver (
    driver_key INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id TEXT UNIQUE NOT NULL,
    name TEXT,
    depot_id TEXT,
    experience_years INTEGER,
    shift TEXT
);

CREATE TABLE dim_route (
    route_key INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id TEXT UNIQUE NOT NULL,
    origin TEXT,
    destination TEXT,
    distance_km REAL,
    expected_duration_min REAL
);

CREATE TABLE dim_customer (
    customer_key INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT UNIQUE NOT NULL,
    customer_name TEXT,
    city TEXT,
    service_area TEXT
);

CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    date TEXT UNIQUE NOT NULL,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    quarter INTEGER
);

CREATE TABLE fact_trip (
    trip_key INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id TEXT,
    timestamp TEXT,
    latitude REAL,
    longitude REAL,
    speed REAL
);

CREATE TABLE fact_delivery (
    delivery_key INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE NOT NULL,
    customer_id TEXT,
    route_id TEXT,
    vehicle_id TEXT,
    driver_id TEXT,
    promised_time TEXT,
    status TEXT,
    scan_time TEXT,
    scan_status TEXT,
    location TEXT
);

CREATE TABLE fact_fuel (
    fuel_key INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id TEXT,
    timestamp TEXT,
    liters REAL,
    amount REAL,
    fuel_type TEXT,
    odometer_km REAL
);

CREATE TABLE fact_maintenance (
    maintenance_key INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id TEXT UNIQUE NOT NULL,
    vehicle_id TEXT,
    issue TEXT,
    opened_at TEXT,
    closed_at TEXT,
    priority TEXT,
    cost REAL,
    downtime_hours REAL
);

CREATE TABLE fact_gps (
    gps_key INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id TEXT,
    timestamp TEXT,
    latitude REAL,
    longitude REAL,
    speed REAL
);

CREATE TABLE fact_vehicle_telemetry (
    telemetry_key INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id TEXT,
    timestamp TEXT,
    engine_status TEXT,
    fuel_level_percent REAL,
    remaining_fuel_liters REAL,
    odometer_km REAL
);
""")

# ============================================================
# GENERIC CSV LOADER
# ============================================================

def load_csv(filename, table, source_columns, target_columns=None):

    if target_columns is None:
        target_columns = source_columns

    path = RAW / filename

    with open(path, "r", encoding="utf-8", newline="") as f:

        reader = csv.DictReader(f)

        rows = []

        for row in reader:
            rows.append(
                tuple(row.get(column, "") for column in source_columns)
            )

    placeholders = ",".join(["?"] * len(target_columns))

    cur.executemany(
        f"""
        INSERT INTO {table}
        ({','.join(target_columns)})
        VALUES ({placeholders})
        """,
        rows
    )

    print(f"{filename}: {len(rows)} records loaded")


# ============================================================
# DIMENSIONS
# ============================================================

load_csv(
    "depots.csv",
    "dim_depot",
    ["depot_id", "depot_name", "city", "capacity"]
)

load_csv(
    "vehicles.csv",
    "dim_vehicle",
    [
        "vehicle_id",
        "type",
        "depot",
        "capacity",
        "model",
        "fuel_capacity_liters"
    ],
    [
        "vehicle_id",
        "type",
        "depot_id",
        "capacity",
        "model",
        "fuel_capacity_liters"
    ]
)

load_csv(
    "drivers.csv",
    "dim_driver",
    [
        "driver_id",
        "name",
        "depot",
        "experience_years",
        "shift"
    ],
    [
        "driver_id",
        "name",
        "depot_id",
        "experience_years",
        "shift"
    ]
)

load_csv(
    "routes.csv",
    "dim_route",
    [
        "route_id",
        "origin",
        "destination",
        "distance_km",
        "expected_duration_min"
    ]
)

load_csv(
    "customers.csv",
    "dim_customer",
    [
        "customer_id",
        "customer_name",
        "city",
        "service_area"
    ]
)

# ============================================================
# DATE DIMENSION
# ============================================================

dates = set()

with open(
    RAW / "orders.csv",
    "r",
    encoding="utf-8",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        promised_time = row["promised_time"]

        if promised_time:
            dates.add(promised_time[:10])


for date_text in sorted(dates):

    year, month, day = map(
        int,
        date_text.split("-")
    )

    quarter = ((month - 1) // 3) + 1

    date_key = int(
        date_text.replace("-", "")
    )

    cur.execute(
        """
        INSERT OR IGNORE INTO dim_date
        (date_key, date, year, month, day, quarter)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            date_key,
            date_text,
            year,
            month,
            day,
            quarter
        )
    )

print(f"dim_date: {len(dates)} dates loaded")


# ============================================================
# DELIVERY SCANS
# ============================================================

scans = {}

with open(
    RAW / "delivery_scans.csv",
    "r",
    encoding="utf-8",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:
        scans[row["order_id"]] = row


# ============================================================
# FACT DELIVERY
# ============================================================

delivery_rows = []

with open(
    RAW / "orders.csv",
    "r",
    encoding="utf-8",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        scan = scans.get(
            row["order_id"],
            {}
        )

        delivery_rows.append(
            (
                row["order_id"],
                row["customer_id"],
                row["route_id"],
                row["vehicle_id"],
                row["driver_id"],
                row["promised_time"],
                row["status"],
                scan.get("scan_time", ""),
                scan.get("status", ""),
                scan.get("location", "")
            )
        )


cur.executemany(
    """
    INSERT INTO fact_delivery
    (
        order_id,
        customer_id,
        route_id,
        vehicle_id,
        driver_id,
        promised_time,
        status,
        scan_time,
        scan_status,
        location
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    delivery_rows
)

print(
    f"fact_delivery: {len(delivery_rows)} records loaded"
)


# ============================================================
# FACT FUEL
# ============================================================

load_csv(
    "fuel.csv",
    "fact_fuel",
    [
        "vehicle_id",
        "timestamp",
        "liters",
        "amount",
        "fuel_type",
        "odometer_km"
    ]
)


# ============================================================
# FACT MAINTENANCE
# ============================================================

maintenance_rows = []

with open(
    RAW / "maintenance.csv",
    "r",
    encoding="utf-8",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        opened = datetime.fromisoformat(
            row["opened_at"]
        )

        closed = datetime.fromisoformat(
            row["closed_at"]
        )

        downtime = (
            closed - opened
        ).total_seconds() / 3600

        maintenance_rows.append(
            (
                row["work_order_id"],
                row["vehicle_id"],
                row["issue"],
                row["opened_at"],
                row["closed_at"],
                row["priority"],
                row["cost"],
                round(downtime, 2)
            )
        )


cur.executemany(
    """
    INSERT INTO fact_maintenance
    (
        work_order_id,
        vehicle_id,
        issue,
        opened_at,
        closed_at,
        priority,
        cost,
        downtime_hours
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
    maintenance_rows
)

print(
    f"fact_maintenance: {len(maintenance_rows)} records loaded"
)


# ============================================================
# FACT GPS
# ============================================================

load_csv(
    "gps.csv",
    "fact_gps",
    [
        "vehicle_id",
        "timestamp",
        "latitude",
        "longitude",
        "speed"
    ]
)


# ============================================================
# FACT TRIP
# ============================================================

# The assignment requires a fact_trip table.
# We populate it from the GPS trip-event data.

cur.execute(
    """
    INSERT INTO fact_trip
    (
        vehicle_id,
        timestamp,
        latitude,
        longitude,
        speed
    )
    SELECT
        vehicle_id,
        timestamp,
        latitude,
        longitude,
        speed
    FROM fact_gps
    """
)

trip_count = cur.execute(
    "SELECT COUNT(*) FROM fact_trip"
).fetchone()[0]

print(
    f"fact_trip: {trip_count} records loaded"
)


# ============================================================
# VEHICLE TELEMETRY
# ============================================================

load_csv(
    "vehicle_telemetry.csv",
    "fact_vehicle_telemetry",
    [
        "vehicle_id",
        "timestamp",
        "engine_status",
        "fuel_level_percent",
        "remaining_fuel_liters",
        "odometer_km"
    ]
)


# ============================================================
# INDEXES
# ============================================================

cur.executescript(
    """
    CREATE INDEX idx_trip_vehicle_time
    ON fact_trip(vehicle_id, timestamp);

    CREATE INDEX idx_gps_vehicle_time
    ON fact_gps(vehicle_id, timestamp);

    CREATE INDEX idx_delivery_vehicle
    ON fact_delivery(vehicle_id);

    CREATE INDEX idx_delivery_route
    ON fact_delivery(route_id);

    CREATE INDEX idx_fuel_vehicle_time
    ON fact_fuel(vehicle_id, timestamp);

    CREATE INDEX idx_maintenance_vehicle
    ON fact_maintenance(vehicle_id);

    CREATE INDEX idx_telemetry_vehicle_time
    ON fact_vehicle_telemetry(vehicle_id, timestamp);
    """
)


# ============================================================
# COMMIT
# ============================================================

conn.commit()


# ============================================================
# FINAL VALIDATION
# ============================================================

print()
print("====================================")
print("FleetVision360 warehouse created!")
print("====================================")
print()

tables = [
    "dim_depot",
    "dim_vehicle",
    "dim_driver",
    "dim_route",
    "dim_customer",
    "dim_date",
    "fact_trip",
    "fact_delivery",
    "fact_fuel",
    "fact_maintenance",
    "fact_gps",
    "fact_vehicle_telemetry"
]

for table in tables:

    count = cur.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(
        f"{table}: {count:,} records"
    )

print()
print(f"Database: {DB}")
print("====================================")

conn.close()