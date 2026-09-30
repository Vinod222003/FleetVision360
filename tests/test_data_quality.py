import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(r"C:\Users\User\FleetVision360\.env")

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def test_vehicle_count():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM dim_vehicle")
    count = cur.fetchone()[0]

    assert count > 0

    cur.close()
    conn.close()


def test_vehicle_ids_not_null():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM dim_vehicle
        WHERE vehicle_id IS NULL
    """)

    null_count = cur.fetchone()[0]

    assert null_count == 0

    cur.close()
    conn.close()


def test_vehicle_ids_unique():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT vehicle_id, COUNT(*)
        FROM dim_vehicle
        GROUP BY vehicle_id
        HAVING COUNT(*) > 1
    """)

    duplicates = cur.fetchall()

    assert len(duplicates) == 0

    cur.close()
    conn.close()


def test_fact_gps_vehicle_reference():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM fact_gps g
        LEFT JOIN dim_vehicle v
            ON g.vehicle_id = v.vehicle_id
        WHERE v.vehicle_id IS NULL
    """)

    invalid_rows = cur.fetchone()[0]

    assert invalid_rows == 0

    cur.close()
    conn.close()


def test_gps_speed_range():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM fact_gps
        WHERE speed < 0 OR speed > 200
    """)

    invalid_rows = cur.fetchone()[0]

    assert invalid_rows == 0

    cur.close()
    conn.close()


def test_fact_delivery_not_empty():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fact_delivery")
    count = cur.fetchone()[0]

    assert count > 0

    cur.close()
    conn.close()


def test_fact_fuel_not_empty():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fact_fuel")
    count = cur.fetchone()[0]

    assert count > 0

    cur.close()
    conn.close()


def test_fact_maintenance_not_empty():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fact_maintenance")
    count = cur.fetchone()[0]

    assert count > 0

    cur.close()
    conn.close()