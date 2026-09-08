"""
Apache Airflow DAG: Student Performance Data Pipeline
-----------------------------------------------------
Orchestrates the end-to-end data engineering pipeline:
1. Ingestion of raw UCI datasets (Math & Portuguese)
2. Validation & Quarantining of corrupted/duplicate records
3. Transformation & Feature Engineering
4. Loading into PostgreSQL Database (students, academic_performance)
5. Construction and verification of Analytical Data Mart
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Ensure src modules are resolvable by Airflow
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Attempt importing Airflow operators (fallback to standalone mock for local CLI test)
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    try:
        from airflow.operators.empty import EmptyOperator
    except ImportError:
        from airflow.operators.dummy import DummyOperator as EmptyOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False


# Task Functions
def task_ingest(**context):
    from src.ingestion.ingest import ingest_all
    summary = ingest_all()
    print(f"Ingestion Task Completed: {summary}")
    return summary


def task_validate(**context):
    from src.validation.validate import run_validation
    summary = run_validation()
    print(f"Validation Task Completed: {summary}")
    return summary


def task_transform(**context):
    from src.transformation.transform import run_transformation
    summary = run_transformation()
    print(f"Transformation Task Completed: {summary}")
    return summary


def task_load_postgres(**context):
    from src.database.load import run_database_load
    summary = run_database_load()
    print(f"Database Load Task Completed: {summary}")
    return summary


def task_build_analytics(**context):
    from src.database.load import query_analytics_data
    df_mart = query_analytics_data()
    print(f"Analytics Data Mart Built Successfully. Total Records: {len(df_mart)}")
    return {"analytics_records": len(df_mart)}


# Airflow DAG Definition
default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

if AIRFLOW_AVAILABLE:
    with DAG(
        dag_id="student_data_pipeline",
        default_args=default_args,
        description="End-to-end Student Performance Data Pipeline (Part 1)",
        schedule_interval="@daily",
        catchup=False,
        tags=["mlops", "data_engineering", "student_performance"],
    ) as dag:

        start_pipeline = EmptyOperator(
            task_id="start_pipeline",
            doc_md="Start marker for student performance data pipeline"
        )

        ingest_raw_data = PythonOperator(
            task_id="ingest_raw_data",
            python_callable=task_ingest,
            doc_md="Ingest raw CSV files from source and record audit metadata"
        )

        validate_and_quarantine = PythonOperator(
            task_id="validate_and_quarantine",
            python_callable=task_validate,
            doc_md="Validate missing values, range 0-20, domain checks and quarantine rejected records"
        )

        transform_features = PythonOperator(
            task_id="transform_features",
            python_callable=task_transform,
            doc_md="Compute academic indicators: avg_grade, pass_fail, attendance_rate, risk_status"
        )

        load_postgresql_tables = PythonOperator(
            task_id="load_postgresql_tables",
            python_callable=task_load_postgres,
            doc_md="Load cleaned records into PostgreSQL dimensional and fact tables"
        )

        build_analytics_mart = PythonOperator(
            task_id="build_analytics_mart",
            python_callable=task_build_analytics,
            doc_md="Generate and verify denormalized analytical table and views"
        )

        pipeline_complete = EmptyOperator(
            task_id="pipeline_complete",
            doc_md="End marker indicating successful pipeline execution"
        )

        # DAG Workflow Sequence
        start_pipeline >> ingest_raw_data >> validate_and_quarantine >> transform_features >> load_postgresql_tables >> build_analytics_mart >> pipeline_complete


# Standalone runner for local testing without active Airflow server
def run_standalone_pipeline():
    """Run full DAG sequence sequentially via Python CLI."""
    print("=" * 70)
    print("EXECUTING STANDALONE PIPELINE WORKFLOW (Airflow DAG Simulation)")
    print("=" * 70)
    
    print("\n[Step 1/5] Ingesting Raw Data...")
    task_ingest()

    print("\n[Step 2/5] Validating & Quarantining Records...")
    task_validate()

    print("\n[Step 3/5] Transforming & Engineering Academic Features...")
    task_transform()

    print("\n[Step 4/5] Loading into PostgreSQL / Relational Database...")
    task_load_postgres()

    print("\n[Step 5/5] Building & Verifying Analytics Data Mart...")
    task_build_analytics()

    print("\n" + "=" * 70)
    print("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_standalone_pipeline()
