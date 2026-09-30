@'
# FleetVision 360

FleetVision 360 is a fleet intelligence and analytics platform for monitoring vehicles, drivers, routes, deliveries, fuel, maintenance, and GPS activity.

## Key Features

- Executive fleet dashboard
- Live fleet monitoring
- GPS fleet map
- Fleet status
- Route management and analytics
- Delivery performance
- Fuel records and analytics
- Maintenance records and analytics
- ML-based fuel prediction
- Data-quality validation
- Automated Airflow pipeline
- Kafka event streaming
- PySpark Bronze-to-Silver processing
- FastAPI backend
- React + Vite frontend
- PostgreSQL analytical warehouse
- GitHub Actions CI

## Technology Stack

### Backend
- Python
- FastAPI
- PostgreSQL
- psycopg2
- SQL

### Data Engineering
- Apache Kafka
- PySpark
- Apache Airflow
- Bronze and Silver data layers

### Machine Learning
- Python
- scikit-learn
- Random Forest fuel prediction

### Frontend
- React
- Vite
- Recharts
- Leaflet

### DevOps
- Docker
- Git
- GitHub Actions CI

## Architecture

Source and simulated fleet events enter the platform through Kafka.

Kafka events are stored in the Bronze layer.

PySpark processes Bronze data into the Silver layer.

Airflow orchestrates the data pipeline.

PostgreSQL stores the analytical warehouse containing vehicle, driver, route, delivery, fuel, maintenance, GPS, and telemetry data.

FastAPI provides backend APIs.

The React frontend consumes the APIs and displays fleet intelligence dashboards.

Machine-learning functionality provides fuel prediction.

Data-quality tests validate important warehouse conditions.

## Project Structure

FleetVision360/
- backend/
- frontend/
- data/
- kafka_streaming/
- gps_simulator/
- pyspark_processing/
- airflow/
- dbt/
- ml/
- scripts/
- sql/
- tests/
- docs/
- .github/
- README.md

## Important Endpoints

- `/api/health`
- `/api/dashboard`
- `/api/fleet/live`
- `/api/fleet/status`
- `/api/routes`
- `/api/fuel`
- `/api/fuel/analytics`
- `/api/maintenance`
- `/api/maintenance/analytics`
- `/api/delivery-performance`
- `/api/silver/gps`
- `/api/ml/fuel-prediction`
- `/api/data-quality`

## Data Quality

The project includes automated tests covering:

- Vehicle availability
- Null vehicle IDs
- Duplicate vehicle IDs
- GPS vehicle reference integrity
- GPS speed range
- Delivery data availability
- Fuel data availability
- Maintenance data availability

## Recovery

Recovery instructions for Kafka, Airflow, PostgreSQL, PySpark, FastAPI, data quality, and frontend services are documented in:

`docs/RECOVERY_PROCEDURE.md`

## CI

GitHub Actions workflow:

`.github/workflows/ci.yml`

The workflow checks Python syntax and verifies data-quality test collection.

## Local Startup

### Backend

    cd C:\Users\User\FleetVision360
    .\.venv\Scripts\Activate.ps1
    uvicorn backend.main:app --reload --port 8000

### Frontend

    cd C:\Users\User\FleetVision360\frontend
    npm run dev

Frontend:

    http://localhost:5173

Backend:

    http://127.0.0.1:8000
'@ | Set-Content C:\Users\User\FleetVision360\README.md