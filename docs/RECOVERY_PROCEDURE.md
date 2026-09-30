# FleetVision 360 - Recovery Procedure

## 1. Kafka Failure

Check Kafka services and restart them if required.

Verify these Kafka topics:

- gps-events
- delivery-events
- vehicle-events

After Kafka is running, verify that events are being produced and consumed.

---

## 2. Airflow Failure

Check Airflow containers:

    docker compose -f airflow\docker-compose.airflow.yml ps

Check scheduler logs:

    docker compose -f airflow\docker-compose.airflow.yml logs airflow-scheduler --tail 100

If required, restart Airflow:

    docker compose -f airflow\docker-compose.airflow.yml restart

Verify the fleetvision_pipeline DAG.

---

## 3. PostgreSQL Failure

Check PostgreSQL:

    Get-Service postgresql-x64-18

If stopped:

    Start-Service postgresql-x64-18

Verify the API:

    http://127.0.0.1:8000/api/health

Expected result:

    {"status":"healthy","database":true}

---

## 4. PySpark Failure

Check the Airflow task logs.

Verify:

- Bronze input files exist.
- PySpark processing files exist.
- Silver output is available.

After correcting the problem, rerun the failed Airflow task or DAG.

---

## 5. FastAPI Failure

Start the backend:

    cd C:\Users\User\FleetVision360
    .\.venv\Scripts\Activate.ps1
    uvicorn backend.main:app --reload --port 8000

Verify:

    http://127.0.0.1:8000/api/health

Expected result:

    {"status":"healthy","database":true}

---

## 6. Data Quality Failure

Run:

    cd C:\Users\User\FleetVision360
    .\.venv\Scripts\Activate.ps1
    python -m pytest tests\test_data_quality.py -v

All data-quality tests should pass.

Also verify:

    http://127.0.0.1:8000/api/data-quality

Expected status:

    {"status":"healthy"}

---

## 7. Frontend Failure

Start the frontend:

    cd C:\Users\User\FleetVision360\frontend
    npm run dev

Open:

    http://localhost:5173

Verify that the dashboard loads and can communicate with FastAPI.

---

## 8. Final Verification

After recovery, verify:

1. PostgreSQL is running.
2. Airflow is running.
3. Kafka is running.
4. Bronze and Silver data are available.
5. Data-quality tests pass.
6. FastAPI /api/health returns healthy.
7. FastAPI /api/data-quality returns healthy.
8. React dashboard loads successfully.
