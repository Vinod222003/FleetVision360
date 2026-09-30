from datetime import datetime
import subprocess

from airflow import DAG
from airflow.operators.python import PythonOperator


def start_pipeline():
    print("FleetVision 360 pipeline started")


def process_bronze_to_silver():
    print("Running actual PySpark Bronze to Silver processing")

    subprocess.run(
        [
            "python",
            "/opt/airflow/pyspark_processing/bronze_to_silver.py"
        ],
        check=True
    )


def finish_pipeline():
    print("FleetVision 360 pipeline completed")


with DAG(
    dag_id="fleetvision_pipeline",
    start_date=datetime(2026, 9, 30),
    schedule=None,
    catchup=False,
) as dag:

    start = PythonOperator(
        task_id="start_pipeline",
        python_callable=start_pipeline,
    )

    bronze_to_silver = PythonOperator(
        task_id="bronze_to_silver",
        python_callable=process_bronze_to_silver,
    )

    finish = PythonOperator(
        task_id="finish_pipeline",
        python_callable=finish_pipeline,
    )

    start >> bronze_to_silver >> finish