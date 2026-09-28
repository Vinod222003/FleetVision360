import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "warehouse" / "fleetvision360.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

print()
print("==============================================")
print(" FleetVision360 - DATA QUALITY CHECK")
print("==============================================")
print()

# ------------------------------------------------
# 1. TABLE VOLUME CHECK
# ------------------------------------------------

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

print("1. TABLE VOLUME CHECK")
print("----------------------------------------------")

for table in tables:
    count = cur.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    status = "PASS" if count > 0 else "FAIL"

    print(f"{table:<30} {count:>8,}  [{status}]")

print()


# ------------------------------------------------
# 2. NULL CHECKS
# ------------------------------------------------

print("2. NULL CHECKS")
print("----------------------------------------------")

null_checks = {
    "dim_vehicle.vehicle_id":
        "SELECT COUNT(*) FROM dim_vehicle WHERE vehicle_id IS NULL OR vehicle_id = ''",

    "dim_driver.driver_id":
        "SELECT COUNT(*) FROM dim_driver WHERE driver_id IS NULL OR driver_id = ''",

    "dim_route.route_id":
        "SELECT COUNT(*) FROM dim_route WHERE route_id IS NULL OR route_id = ''",

    "dim_customer.customer_id":
        "SELECT COUNT(*) FROM dim_customer WHERE customer_id IS NULL OR customer_id = ''",

    "fact_delivery.order_id":
        "SELECT COUNT(*) FROM fact_delivery WHERE order_id IS NULL OR order_id = ''",

    "fact_fuel.vehicle_id":
        "SELECT COUNT(*) FROM fact_fuel WHERE vehicle_id IS NULL OR vehicle_id = ''",

    "fact_maintenance.work_order_id":
        "SELECT COUNT(*) FROM fact_maintenance WHERE work_order_id IS NULL OR work_order_id = ''",

    "fact_gps.vehicle_id":
        "SELECT COUNT(*) FROM fact_gps WHERE vehicle_id IS NULL OR vehicle_id = ''"
}

for name, query in null_checks.items():

    count = cur.execute(query).fetchone()[0]

    status = "PASS" if count == 0 else "FAIL"

    print(f"{name:<40} {count:>6} [{status}]")

print()


# ------------------------------------------------
# 3. DUPLICATE / UNIQUENESS CHECK
# ------------------------------------------------

print("3. UNIQUENESS CHECKS")
print("----------------------------------------------")

unique_checks = {
    "dim_vehicle.vehicle_id":
        """
        SELECT COUNT(*) - COUNT(DISTINCT vehicle_id)
        FROM dim_vehicle
        """,

    "dim_driver.driver_id":
        """
        SELECT COUNT(*) - COUNT(DISTINCT driver_id)
        FROM dim_driver
        """,

    "dim_route.route_id":
        """
        SELECT COUNT(*) - COUNT(DISTINCT route_id)
        FROM dim_route
        """,

    "dim_customer.customer_id":
        """
        SELECT COUNT(*) - COUNT(DISTINCT customer_id)
        FROM dim_customer
        """,

    "fact_delivery.order_id":
        """
        SELECT COUNT(*) - COUNT(DISTINCT order_id)
        FROM fact_delivery
        """,

    "fact_maintenance.work_order_id":
        """
        SELECT COUNT(*) - COUNT(DISTINCT work_order_id)
        FROM fact_maintenance
        """
}

for name, query in unique_checks.items():

    duplicates = cur.execute(query).fetchone()[0]

    status = "PASS" if duplicates == 0 else "FAIL"

    print(
        f"{name:<40} "
        f"{duplicates:>6} duplicates [{status}]"
    )

print()


# ------------------------------------------------
# 4. REFERENTIAL INTEGRITY
# ------------------------------------------------

print("4. REFERENTIAL INTEGRITY")
print("----------------------------------------------")

integrity_checks = {

    "delivery -> vehicle":
        """
        SELECT COUNT(*)
        FROM fact_delivery f
        LEFT JOIN dim_vehicle d
        ON f.vehicle_id = d.vehicle_id
        WHERE d.vehicle_id IS NULL
        """,

    "delivery -> driver":
        """
        SELECT COUNT(*)
        FROM fact_delivery f
        LEFT JOIN dim_driver d
        ON f.driver_id = d.driver_id
        WHERE d.driver_id IS NULL
        """,

    "delivery -> route":
        """
        SELECT COUNT(*)
        FROM fact_delivery f
        LEFT JOIN dim_route r
        ON f.route_id = r.route_id
        WHERE r.route_id IS NULL
        """,

    "delivery -> customer":
        """
        SELECT COUNT(*)
        FROM fact_delivery f
        LEFT JOIN dim_customer c
        ON f.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
        """,

    "fuel -> vehicle":
        """
        SELECT COUNT(*)
        FROM fact_fuel f
        LEFT JOIN dim_vehicle v
        ON f.vehicle_id = v.vehicle_id
        WHERE v.vehicle_id IS NULL
        """,

    "maintenance -> vehicle":
        """
        SELECT COUNT(*)
        FROM fact_maintenance f
        LEFT JOIN dim_vehicle v
        ON f.vehicle_id = v.vehicle_id
        WHERE v.vehicle_id IS NULL
        """,

    "gps -> vehicle":
        """
        SELECT COUNT(*)
        FROM fact_gps f
        LEFT JOIN dim_vehicle v
        ON f.vehicle_id = v.vehicle_id
        WHERE v.vehicle_id IS NULL
        """
}

for name, query in integrity_checks.items():

    orphan_count = cur.execute(query).fetchone()[0]

    status = "PASS" if orphan_count == 0 else "FAIL"

    print(
        f"{name:<30} "
        f"{orphan_count:>6} orphan records [{status}]"
    )

print()


# ------------------------------------------------
# 5. RANGE / BUSINESS RULE CHECKS
# ------------------------------------------------

print("5. RANGE / BUSINESS RULE CHECKS")
print("----------------------------------------------")

range_checks = {

    "GPS latitude":
        """
        SELECT COUNT(*)
        FROM fact_gps
        WHERE latitude < -90 OR latitude > 90
        """,

    "GPS longitude":
        """
        SELECT COUNT(*)
        FROM fact_gps
        WHERE longitude < -180 OR longitude > 180
        """,

    "GPS speed":
        """
        SELECT COUNT(*)
        FROM fact_gps
        WHERE speed < 0
        """,

    "Fuel liters":
        """
        SELECT COUNT(*)
        FROM fact_fuel
        WHERE liters <= 0
        """,

    "Fuel amount":
        """
        SELECT COUNT(*)
        FROM fact_fuel
        WHERE amount < 0
        """,

    "Telemetry fuel %":
        """
        SELECT COUNT(*)
        FROM fact_vehicle_telemetry
        WHERE fuel_level_percent < 0
           OR fuel_level_percent > 100
        """,

    "Telemetry remaining fuel":
        """
        SELECT COUNT(*)
        FROM fact_vehicle_telemetry
        WHERE remaining_fuel_liters < 0
        """,

    "Maintenance cost":
        """
        SELECT COUNT(*)
        FROM fact_maintenance
        WHERE cost < 0
        """,

    "Maintenance downtime":
        """
        SELECT COUNT(*)
        FROM fact_maintenance
        WHERE downtime_hours < 0
        """
}

for name, query in range_checks.items():

    invalid = cur.execute(query).fetchone()[0]

    status = "PASS" if invalid == 0 else "FAIL"

    print(
        f"{name:<35} "
        f"{invalid:>6} invalid [{status}]"
    )

print()


# ------------------------------------------------
# FINAL RESULT
# ------------------------------------------------

print("==============================================")
print(" DATA QUALITY CHECK COMPLETE")
print("==============================================")

conn.close()