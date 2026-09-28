import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "warehouse" / "fleetvision360.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

print()
print("======================================================")
print(" FleetVision360 - GOVERNED ANALYTICAL / KPI LAYER")
print("======================================================")
print()

cur.executescript("""

DROP VIEW IF EXISTS vw_exceptions;
DROP VIEW IF EXISTS vw_depot_performance;
DROP VIEW IF EXISTS vw_vehicle_kpi;
DROP VIEW IF EXISTS vw_route_performance;
DROP VIEW IF EXISTS vw_maintenance_kpi;
DROP VIEW IF EXISTS vw_fuel_efficiency;
DROP VIEW IF EXISTS vw_idle_time;
DROP VIEW IF EXISTS vw_cost_per_delivery;
DROP VIEW IF EXISTS vw_delivery_trend;
DROP VIEW IF EXISTS vw_executive_kpis;


-- ======================================================
-- 1. ON-TIME DELIVERY
-- ======================================================

CREATE VIEW vw_delivery_trend AS
SELECT
    substr(promised_time, 1, 10) AS date,

    COUNT(*) AS total_deliveries,

    SUM(
        CASE
            WHEN LOWER(status) = 'delivered'
            THEN 1 ELSE 0
        END
    ) AS delivered,

    SUM(
        CASE
            WHEN LOWER(status) = 'delayed'
            THEN 1 ELSE 0
        END
    ) AS delayed,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN LOWER(status) = 'delivered'
                THEN 1 ELSE 0
            END
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS on_time_rate,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN LOWER(status) = 'delayed'
                THEN 1 ELSE 0
            END
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS delay_rate

FROM fact_delivery

GROUP BY substr(promised_time, 1, 10);


-- ======================================================
-- 2. FUEL EFFICIENCY
-- ======================================================

CREATE VIEW vw_fuel_efficiency AS
SELECT
    f.vehicle_id,

    ROUND(SUM(f.liters), 2) AS fuel_liters,

    ROUND(
        MAX(f.odometer_km) - MIN(f.odometer_km),
        2
    ) AS distance_km,

    ROUND(
        (
            MAX(f.odometer_km) - MIN(f.odometer_km)
        ) / NULLIF(SUM(f.liters), 0),
        2
    ) AS km_per_liter,

    ROUND(SUM(f.amount), 2) AS fuel_cost,

    COUNT(*) AS fuel_events

FROM fact_fuel f

GROUP BY f.vehicle_id;


-- ======================================================
-- 3. COST PER DELIVERY
-- ======================================================

CREATE VIEW vw_cost_per_delivery AS
SELECT
    v.vehicle_id,

    COALESCE(f.fuel_cost, 0) AS fuel_cost,

    COALESCE(d.delivery_count, 0) AS deliveries,

    ROUND(
        COALESCE(f.fuel_cost, 0)
        / NULLIF(COALESCE(d.delivery_count, 0), 0),
        2
    ) AS cost_per_delivery

FROM dim_vehicle v

LEFT JOIN
(
    SELECT
        vehicle_id,
        SUM(amount) AS fuel_cost
    FROM fact_fuel
    GROUP BY vehicle_id
) f
ON v.vehicle_id = f.vehicle_id

LEFT JOIN
(
    SELECT
        vehicle_id,
        COUNT(*) AS delivery_count
    FROM fact_delivery
    GROUP BY vehicle_id
) d
ON v.vehicle_id = d.vehicle_id;


-- ======================================================
-- 4. IDLE TIME
-- ======================================================
-- Telemetry records with engine running but speed effectively
-- stationary are treated as idle events.

CREATE VIEW vw_idle_time AS
SELECT
    vehicle_id,

    COUNT(*) AS telemetry_events,

    SUM(
        CASE
            WHEN LOWER(engine_status) = 'on'
            AND fuel_level_percent >= 0
            THEN 1
            ELSE 0
        END
    ) AS engine_on_events,

    SUM(
        CASE
            WHEN LOWER(engine_status) = 'on'
            AND odometer_km IS NOT NULL
            THEN 1
            ELSE 0
        END
    ) AS active_engine_events

FROM fact_vehicle_telemetry

GROUP BY vehicle_id;


-- ======================================================
-- 5. MAINTENANCE DOWNTIME
-- ======================================================

CREATE VIEW vw_maintenance_kpi AS
SELECT
    vehicle_id,

    COUNT(*) AS work_orders,

    ROUND(SUM(downtime_hours), 2)
        AS downtime_hours,

    ROUND(AVG(downtime_hours), 2)
        AS average_downtime_hours,

    ROUND(SUM(cost), 2)
        AS maintenance_cost,

    SUM(
        CASE
            WHEN LOWER(priority) = 'high'
            THEN 1 ELSE 0
        END
    ) AS high_priority_orders

FROM fact_maintenance

GROUP BY vehicle_id;


-- ======================================================
-- 6. ROUTE PERFORMANCE
-- ======================================================

CREATE VIEW vw_route_performance AS
SELECT
    r.route_id,
    r.origin,
    r.destination,
    r.distance_km,
    r.expected_duration_min,

    COUNT(d.order_id) AS total_orders,

    SUM(
        CASE
            WHEN LOWER(d.status) = 'delivered'
            THEN 1 ELSE 0
        END
    ) AS delivered_orders,

    SUM(
        CASE
            WHEN LOWER(d.status) = 'delayed'
            THEN 1 ELSE 0
        END
    ) AS delayed_orders,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN LOWER(d.status) = 'delayed'
                THEN 1 ELSE 0
            END
        )
        / NULLIF(COUNT(d.order_id), 0),
        2
    ) AS delay_rate

FROM dim_route r

LEFT JOIN fact_delivery d
ON r.route_id = d.route_id

GROUP BY
    r.route_id,
    r.origin,
    r.destination,
    r.distance_km,
    r.expected_duration_min;


-- ======================================================
-- 7. VEHICLE KPI / UTILIZATION
-- ======================================================

CREATE VIEW vw_vehicle_kpi AS
SELECT
    v.vehicle_id,
    v.type,
    v.model,
    v.depot_id,
    v.capacity,

    COUNT(DISTINCT d.order_id)
        AS deliveries,

    COUNT(DISTINCT g.timestamp)
        AS gps_events,

    ROUND(AVG(g.speed), 2)
        AS average_speed,

    ROUND(MAX(g.speed), 2)
        AS maximum_speed,

    COALESCE(fe.km_per_liter, 0)
        AS km_per_liter,

    COALESCE(cp.cost_per_delivery, 0)
        AS cost_per_delivery,

    COALESCE(mi.downtime_hours, 0)
        AS maintenance_downtime_hours

FROM dim_vehicle v

LEFT JOIN fact_delivery d
ON v.vehicle_id = d.vehicle_id

LEFT JOIN fact_gps g
ON v.vehicle_id = g.vehicle_id

LEFT JOIN vw_fuel_efficiency fe
ON v.vehicle_id = fe.vehicle_id

LEFT JOIN vw_cost_per_delivery cp
ON v.vehicle_id = cp.vehicle_id

LEFT JOIN vw_maintenance_kpi mi
ON v.vehicle_id = mi.vehicle_id

GROUP BY
    v.vehicle_id,
    v.type,
    v.model,
    v.depot_id,
    v.capacity,
    fe.km_per_liter,
    cp.cost_per_delivery,
    mi.downtime_hours;


-- ======================================================
-- 8. DEPOT SEGMENTATION
-- ======================================================

CREATE VIEW vw_depot_performance AS

WITH vehicle_counts AS (
    SELECT
        depot_id,
        COUNT(DISTINCT vehicle_id) AS vehicles
    FROM dim_vehicle
    GROUP BY depot_id
),

delivery_counts AS (
    SELECT
        v.depot_id,
        COUNT(DISTINCT d.order_id) AS deliveries
    FROM dim_vehicle v
    LEFT JOIN fact_delivery d
        ON v.vehicle_id = d.vehicle_id
    GROUP BY v.depot_id
),

gps_metrics AS (
    SELECT
        v.depot_id,
        ROUND(AVG(g.speed), 2) AS average_speed
    FROM dim_vehicle v
    LEFT JOIN fact_gps g
        ON v.vehicle_id = g.vehicle_id
    GROUP BY v.depot_id
),

fuel_metrics AS (
    SELECT
        v.depot_id,
        ROUND(SUM(f.amount), 2) AS fuel_cost
    FROM dim_vehicle v
    LEFT JOIN fact_fuel f
        ON v.vehicle_id = f.vehicle_id
    GROUP BY v.depot_id
),

maintenance_metrics AS (
    SELECT
        v.depot_id,
        ROUND(SUM(m.downtime_hours), 2) AS maintenance_downtime
    FROM dim_vehicle v
    LEFT JOIN fact_maintenance m
        ON v.vehicle_id = m.vehicle_id
    GROUP BY v.depot_id
)

SELECT
    vc.depot_id,
    vc.vehicles,
    COALESCE(dc.deliveries, 0) AS deliveries,
    COALESCE(gm.average_speed, 0) AS average_speed,
    COALESCE(fm.fuel_cost, 0) AS fuel_cost,
    COALESCE(mm.maintenance_downtime, 0) AS maintenance_downtime

FROM vehicle_counts vc

LEFT JOIN delivery_counts dc
    ON vc.depot_id = dc.depot_id

LEFT JOIN gps_metrics gm
    ON vc.depot_id = gm.depot_id

LEFT JOIN fuel_metrics fm
    ON vc.depot_id = fm.depot_id

LEFT JOIN maintenance_metrics mm
    ON vc.depot_id = mm.depot_id;

-- ======================================================
-- 9. EXECUTIVE KPI SUMMARY
-- ======================================================

CREATE VIEW vw_executive_kpis AS
SELECT

    (SELECT COUNT(*)
     FROM dim_vehicle)
        AS total_vehicles,

    (SELECT COUNT(*)
     FROM dim_driver)
        AS total_drivers,

    (SELECT COUNT(*)
     FROM dim_route)
        AS total_routes,

    (SELECT COUNT(*)
     FROM fact_delivery)
        AS total_deliveries,

    (SELECT
        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN LOWER(status) = 'delivered'
                    THEN 1 ELSE 0
                END
            )
            / NULLIF(COUNT(*), 0),
            2
        )
     FROM fact_delivery)
        AS on_time_delivery_rate,

    (SELECT
        ROUND(SUM(liters), 2)
     FROM fact_fuel)
        AS total_fuel_liters,

    (SELECT
        ROUND(SUM(amount), 2)
     FROM fact_fuel)
        AS total_fuel_cost,

    (SELECT
        ROUND(
            (
                MAX(odometer_km) - MIN(odometer_km)
            )
            / NULLIF(SUM(liters), 0),
            2
        )
     FROM fact_fuel)
        AS fleet_km_per_liter,

    (SELECT
        ROUND(SUM(amount), 2)
     FROM fact_fuel)
        /
        NULLIF(
            (SELECT COUNT(*)
             FROM fact_delivery),
            0
        )
        AS fleet_cost_per_delivery,

    (SELECT
        ROUND(SUM(downtime_hours), 2)
     FROM fact_maintenance)
        AS total_maintenance_downtime_hours,

    (SELECT COUNT(*)
     FROM fact_maintenance)
        AS total_maintenance_work_orders;


-- ======================================================
-- 10. EXCEPTION ANALYSIS
-- ======================================================

CREATE VIEW vw_exceptions AS

SELECT
    'DELAYED_ROUTE' AS exception_type,
    route_id AS entity_id,
    'HIGH' AS severity,
    delay_rate AS metric_value,
    'Route has elevated delivery delay rate'
        AS description

FROM vw_route_performance

WHERE total_orders > 0
AND delay_rate >= 20

UNION ALL

SELECT
    'LOW_FUEL_EFFICIENCY' AS exception_type,
    vehicle_id AS entity_id,
    'MEDIUM' AS severity,
    km_per_liter AS metric_value,
    'Vehicle has low fuel efficiency'
        AS description

FROM vw_fuel_efficiency

WHERE km_per_liter > 0
AND km_per_liter < 8

UNION ALL

SELECT
    'HIGH_MAINTENANCE_DOWNTIME' AS exception_type,
    vehicle_id AS entity_id,
    'HIGH' AS severity,
    downtime_hours AS metric_value,
    'Vehicle has high maintenance downtime'
        AS description

FROM vw_maintenance_kpi

WHERE downtime_hours >= 24;

""")

conn.commit()


# ======================================================
# PRINT EXECUTIVE KPIs
# ======================================================

print("EXECUTIVE KPIs")
print("------------------------------------------------------")

row = cur.execute(
    "SELECT * FROM vw_executive_kpis"
).fetchone()

columns = [
    description[0]
    for description in cur.description
]

for column, value in zip(columns, row):
    print(f"{column:<38} {value}")

print()


# ======================================================
# TREND ANALYSIS
# ======================================================

print("DELIVERY TREND")
print("------------------------------------------------------")

rows = cur.execute("""
    SELECT
        date,
        total_deliveries,
        delivered,
        delayed,
        on_time_rate,
        delay_rate
    FROM vw_delivery_trend
    ORDER BY date
    LIMIT 20
""").fetchall()

for row in rows:
    print(row)

print()


# ======================================================
# TOP ROUTE EXCEPTIONS
# ======================================================

print("ROUTE EXCEPTIONS")
print("------------------------------------------------------")

rows = cur.execute("""
    SELECT
        route_id,
        origin,
        destination,
        total_orders,
        delayed_orders,
        delay_rate
    FROM vw_route_performance
    WHERE total_orders > 0
    ORDER BY delay_rate DESC
    LIMIT 10
""").fetchall()

for row in rows:
    print(row)

print()


# ======================================================
# VEHICLE DRILL-DOWN
# ======================================================

print("VEHICLE DRILL-DOWN")
print("------------------------------------------------------")

rows = cur.execute("""
    SELECT
        vehicle_id,
        type,
        model,
        depot_id,
        deliveries,
        average_speed,
        km_per_liter,
        cost_per_delivery,
        maintenance_downtime_hours
    FROM vw_vehicle_kpi
    ORDER BY deliveries DESC
    LIMIT 10
""").fetchall()

for row in rows:
    print(row)

print()


# ======================================================
# DEPOT SEGMENTATION
# ======================================================

print("DEPOT SEGMENTATION")
print("------------------------------------------------------")

rows = cur.execute("""
    SELECT
        depot_id,
        vehicles,
        deliveries,
        average_speed,
        fuel_cost,
        maintenance_downtime
    FROM vw_depot_performance
    ORDER BY deliveries DESC
""").fetchall()

for row in rows:
    print(row)

print()


# ======================================================
# EXCEPTION ANALYSIS
# ======================================================

print("EXCEPTION ANALYSIS")
print("------------------------------------------------------")

rows = cur.execute("""
    SELECT
        exception_type,
        entity_id,
        severity,
        metric_value,
        description
    FROM vw_exceptions
    ORDER BY
        CASE severity
            WHEN 'HIGH' THEN 1
            WHEN 'MEDIUM' THEN 2
            ELSE 3
        END,
        metric_value DESC
    LIMIT 20
""").fetchall()

if rows:
    for row in rows:
        print(row)
else:
    print("No exceptions detected.")

print()

print("======================================================")
print(" ANALYTICAL LAYER CREATED SUCCESSFULLY")
print("======================================================")

conn.close()