from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "warehouse" / "fleetvision360.db"


app = FastAPI(
    title="FleetVision 360 API",
    description="Backend API for the FleetVision 360 fleet intelligence platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Warehouse database not found: {DB_PATH}"
        )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def root():
    return {
        "message": "FleetVision 360 API is running",
        "status": "online"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": DB_PATH.exists()
    }


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
                ROUND(SUM(liters), 2) AS total_liters,
                ROUND(SUM(amount), 2) AS total_cost
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
            SELECT
                speed
            FROM fact_gps g
            WHERE g.timestamp = (
                SELECT MAX(g2.timestamp)
                FROM fact_gps g2
                WHERE g2.vehicle_id = g.vehicle_id
            )
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