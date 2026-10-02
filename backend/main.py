from pathlib import Path
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json
import joblib
import numpy as np
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("fleetvision360")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "ml" / "models" / "fuel_prediction_model.pkl"

fuel_model = joblib.load(MODEL_PATH)
load_dotenv(BASE_DIR / ".env")

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


app = FastAPI(
    title="FleetVision 360 API",
    description="Backend API for the FleetVision 360 fleet intelligence platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = round((time.time() - start_time) * 1000, 2)

    logger.info(
        "%s %s | status=%s | duration=%sms",
        request.method,
        request.url.path,
        response.status_code,
        duration
    )

    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PostgreSQLConnection:
    def __init__(self):
        self.conn = psycopg2.connect(
            **POSTGRES_CONFIG
        )

    def execute(self, query, params=None):
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or ())
        return cursor

    def cursor(self):
        return self.conn.cursor()
    def close(self):
        self.conn.close()

def get_db():
    try:
        return PostgreSQLConnection()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PostgreSQL connection failed: {e}"
        )


@app.get("/")
def root():
    return {
        "message": "FleetVision 360 API is running",
        "status": "online"
    }


@app.get("/api/health")
def health_check():
    conn = None

    try:
        conn = get_db()

        with conn.cursor() as cur:
            cur.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": True
        }

    except Exception:
        return {
            "status": "unhealthy",
            "database": False
        }

    finally:
        if conn:
            conn.close()


@app.get("/api/dashboard")
def dashboard():
    conn = get_db()

    try:
        vehicles = conn.execute(
            "SELECT COUNT(*) AS value FROM dim_vehicle"
        ).fetchone()["value"]

        drivers = conn.execute(
            "SELECT COUNT(*) AS value FROM dim_driver"
        ).fetchone()["value"]

        routes = conn.execute(
            "SELECT COUNT(*) AS value FROM dim_route"
        ).fetchone()["value"]

        deliveries = conn.execute(
            "SELECT COUNT(*) AS value FROM fact_delivery"
        ).fetchone()["value"]

        fuel = conn.execute(
            """
            SELECT
                COALESCE(SUM(liters), 0) AS liters,
                COALESCE(SUM(amount), 0) AS amount
            FROM fact_fuel
            """
        ).fetchone()

        maintenance = conn.execute(
            """
            SELECT
                COALESCE(SUM(downtime_hours), 0) AS downtime_hours,
                COUNT(*) AS work_orders
            FROM fact_maintenance
            """
        ).fetchone()

        delivered = conn.execute(
            """
            SELECT COUNT(*) AS value
            FROM fact_delivery
            WHERE LOWER(status) = 'delivered'
            """
        ).fetchone()["value"]

        on_time = conn.execute(
            """
            SELECT COUNT(*) AS value
            FROM fact_delivery
            WHERE LOWER(status) = 'delivered'
              AND scan_time IS NOT NULL
              AND scan_time != ''
              AND promised_time IS NOT NULL
              AND scan_time <= promised_time
            """
        ).fetchone()["value"]

        on_time_rate = (
            round((on_time / delivered) * 100, 2)
            if delivered
            else 0
        )

        cost_per_delivery = (
            round(fuel["amount"] / deliveries, 2)
            if deliveries
            else 0
        )

        return {
            "vehicles": vehicles,
            "drivers": drivers,
            "routes": routes,
            "deliveries": deliveries,
            "on_time_delivery_rate_percent": on_time_rate,
            "fuel_liters": round(fuel["liters"], 2),
            "fuel_cost": round(fuel["amount"], 2),
            "fuel_cost_per_delivery": cost_per_delivery,
            "maintenance_downtime_hours": round(
                maintenance["downtime_hours"], 2
            ),
            "maintenance_work_orders": maintenance["work_orders"]
        }

    finally:
        conn.close()
@app.get("/api/fleet/live")
def live_fleet():
    conn = get_db()

    try:
        rows = conn.execute(
            """
            SELECT
                v.vehicle_id,
                v.type,
                v.model,
                v.depot_id,
                g.timestamp,
                g.latitude,
                g.longitude,
                g.speed
            FROM dim_vehicle v
            LEFT JOIN fact_gps g
                ON g.vehicle_id = v.vehicle_id
            WHERE g.timestamp = (
                SELECT MAX(g2.timestamp)
                FROM fact_gps g2
                WHERE g2.vehicle_id = v.vehicle_id
            )
            ORDER BY v.vehicle_id
            """
        ).fetchall()

        return {
            "count": len(rows),
            "vehicles": [dict(row) for row in rows]
        }

    finally:
        conn.close()

@app.get("/api/routes")
def get_routes():
    conn = get_db()

    try:
        rows = conn.execute(
            """
            SELECT
                route_key,
                route_id,
                origin,
                destination,
                distance_km,
                expected_duration_min
            FROM dim_route
            ORDER BY route_key
            """
        ).fetchall()

        return {
            "count": len(rows),
            "routes": [dict(row) for row in rows]
        }

    finally:
        conn.close()

@app.get("/api/fuel")
def get_fuel():
    conn = get_db()

    try:
        rows = conn.execute(
            """
            SELECT
                fuel_key,
                vehicle_id,
                timestamp,
                liters,
                amount,
                fuel_type,
                odometer_km
            FROM fact_fuel
            ORDER BY timestamp DESC
            LIMIT 100
            """
        ).fetchall()

        return {
            "count": len(rows),
            "fuel": [dict(row) for row in rows]
        }

    finally:
        conn.close()

@app.get("/api/fuel/analytics")
def fuel_analytics():
    conn = get_db()

    try:
        rows = conn.execute(
            """
            SELECT
                fuel_type,
                ROUND(SUM(liters)::numeric, 2) AS total_liters,
		ROUND(SUM(amount)::numeric, 2) AS total_cost
            FROM fact_fuel
            GROUP BY fuel_type
            ORDER BY total_cost DESC
            """
        ).fetchall()

        return {
            "fuel_analytics": [dict(row) for row in rows]
        }

    finally:
        conn.close()

@app.get("/api/maintenance")
def get_maintenance():
    conn = get_db()

    try:
        rows = conn.execute(
            """
            SELECT
                maintenance_key,
                work_order_id,
                vehicle_id,
                issue,
                opened_at,
                closed_at,
                priority,
                cost,
                downtime_hours
            FROM fact_maintenance
            ORDER BY opened_at DESC
            LIMIT 100
            """
        ).fetchall()

        return {
            "count": len(rows),
            "maintenance": [dict(row) for row in rows]
        }

    finally:
        conn.close()

@app.get("/api/fleet/status")
def fleet_status():
    conn = get_db()

    try:
        rows = conn.execute(
            """
            SELECT speed
	    FROM (
		SELECT DISTINCT ON (vehicle_id)
		    vehicle_id,
                    speed
    		FROM fact_gps
    		ORDER BY vehicle_id, timestamp DESC
            ) latest
            """
        ).fetchall()

        moving = 0
        idle = 0
        stopped = 0

        for row in rows:
            speed = row["speed"] or 0

            if speed > 5:
                moving += 1
            elif speed > 0:
                idle += 1
            else:
                stopped += 1

        return {
            "moving": moving,
            "idle": idle,
            "stopped": stopped,
            "total": len(rows)
        }

    finally:
        conn.close()

@app.get("/api/delivery-performance")
def delivery_performance():
    conn = get_db()

    try:
        row = conn.execute(
            """
            SELECT
                SUM(
                    CASE
                        WHEN scan_status = 'delivered' THEN 1
                        ELSE 0
                    END
                ) AS delivered,
                SUM(
                    CASE
                        WHEN scan_status = 'delayed' THEN 1
                        ELSE 0
                    END
                ) AS delayed
            FROM fact_delivery
            """
        ).fetchone()

        delivered = row["delivered"] or 0
        delayed = row["delayed"] or 0

        completed = delivered + delayed

        on_time_rate = 0

        if completed > 0:
            on_time_rate = round((delivered / completed) * 100, 2)

        return {
            "total_deliveries": completed,
            "delivered": delivered,
            "delayed": delayed,
            "on_time_rate_percent": on_time_rate
        }

    finally:
        conn.close()

@app.get("/api/maintenance/analytics")
def maintenance_analytics():
    conn = get_db()

    try:
        rows = conn.execute(
            """
            SELECT
                priority,
                COUNT(*) AS work_orders,
                ROUND(SUM(cost)::numeric, 2) AS total_cost,
		ROUND(SUM(downtime_hours)::numeric, 2) AS total_downtime_hours
            FROM fact_maintenance
            GROUP BY priority
            ORDER BY total_cost DESC
            """
        ).fetchall()

        return {
            "maintenance_analytics": [dict(row) for row in rows]
        }

    finally:
        conn.close()

@app.get("/api/silver/gps")
def silver_gps():
    silver_file = (
        BASE_DIR
        / "data"
        / "silver"
        / "gps"
        / "gps_data.jsonl"
    )

    if not silver_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Silver GPS file not found: {silver_file}"
        )

    records = []

    try:
        with open(silver_file, "r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    records.append(json.loads(line))

        return {
            "count": len(records),
            "source": "PySpark Silver GPS",
            "gps": records
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/api/ml/fuel-prediction")
def fuel_prediction(
    distance_km: float,
    speed_kmh: float,
    fuel_level: float
):
    try:
        input_data = np.array([[
            distance_km,
            speed_kmh,
            fuel_level
        ]])

        prediction = fuel_model.predict(input_data)[0]

        return {
            "distance_km": distance_km,
            "speed_kmh": speed_kmh,
            "fuel_level": fuel_level,
            "predicted_fuel_consumption": round(float(prediction), 2),
            "model": "Random Forest"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@app.get("/api/data-quality")
def data_quality():
    conn = None

    try:
        conn = get_db()

        checks = {}

        with conn.cursor() as cur:

            # Vehicle count
            cur.execute("SELECT COUNT(*) FROM dim_vehicle")
            checks["vehicle_count"] = cur.fetchone()[0]

            # Null vehicle IDs
            cur.execute("""
                SELECT COUNT(*)
                FROM dim_vehicle
                WHERE vehicle_id IS NULL
            """)
            checks["null_vehicle_ids"] = cur.fetchone()[0]

            # Duplicate vehicle IDs
            cur.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT vehicle_id
                    FROM dim_vehicle
                    GROUP BY vehicle_id
                    HAVING COUNT(*) > 1
                ) duplicates
            """)
            checks["duplicate_vehicle_ids"] = cur.fetchone()[0]

            # Invalid GPS vehicle references
            cur.execute("""
                SELECT COUNT(*)
                FROM fact_gps g
                LEFT JOIN dim_vehicle v
                    ON g.vehicle_id = v.vehicle_id
                WHERE v.vehicle_id IS NULL
            """)
            checks["invalid_gps_vehicle_references"] = cur.fetchone()[0]

            # Invalid GPS speeds
            cur.execute("""
                SELECT COUNT(*)
                FROM fact_gps
                WHERE speed < 0 OR speed > 200
            """)
            checks["invalid_gps_speed"] = cur.fetchone()[0]

            # Delivery records
            cur.execute("SELECT COUNT(*) FROM fact_delivery")
            checks["delivery_count"] = cur.fetchone()[0]

            # Fuel records
            cur.execute("SELECT COUNT(*) FROM fact_fuel")
            checks["fuel_count"] = cur.fetchone()[0]

            # Maintenance records
            cur.execute("SELECT COUNT(*) FROM fact_maintenance")
            checks["maintenance_count"] = cur.fetchone()[0]

        failed_checks = []

        if checks["vehicle_count"] == 0:
            failed_checks.append("vehicle_count")

        if checks["null_vehicle_ids"] > 0:
            failed_checks.append("null_vehicle_ids")

        if checks["duplicate_vehicle_ids"] > 0:
            failed_checks.append("duplicate_vehicle_ids")

        if checks["invalid_gps_vehicle_references"] > 0:
            failed_checks.append("invalid_gps_vehicle_references")

        if checks["invalid_gps_speed"] > 0:
            failed_checks.append("invalid_gps_speed")

        if checks["delivery_count"] == 0:
            failed_checks.append("delivery_count")

        if checks["fuel_count"] == 0:
            failed_checks.append("fuel_count")

        if checks["maintenance_count"] == 0:
            failed_checks.append("maintenance_count")

        return {
            "status": "healthy" if not failed_checks else "warning",
            "checks": checks,
            "failed_checks": failed_checks
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Data quality check failed: {e}"
        )

    finally:
        if conn:
            conn.close()
