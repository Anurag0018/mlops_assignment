"""
Apache Airflow DAG: Student Performance Data Pipeline

Pipeline:
1. Ingest raw UCI datasets
2. Validate and quarantine bad/duplicate records
3. Transform and engineer features
4. Load data into PostgreSQL
5. Build and verify the analytics data mart
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.empty import EmptyOperator


# ============================================================
# Project Path
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Task Functions
# ============================================================

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

    print(
        f"Analytics Data Mart Built Successfully. "
        f"Total Records: {len(df_mart)}"
    )

    return {
        "analytics_records": len(df_mart)
    }


# ============================================================
# Default Arguments
# ============================================================

default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# ============================================================
# DAG Definition
# ============================================================

with DAG(
    dag_id="student_data_pipeline",
    default_args=default_args,
    description="End-to-end Student Performance Data Pipeline (Part 1)",
    schedule="@daily",
    catchup=False,
    tags=[
        "mlops",
        "data_engineering",
        "student_performance",
    ],
) as dag:

    # --------------------------------------------------------
    # 1. Start
    # --------------------------------------------------------

    start_pipeline = EmptyOperator(
        task_id="start_pipeline",
        doc_md="Start marker for student performance data pipeline",
    )

    # --------------------------------------------------------
    # 2. Ingestion
    # --------------------------------------------------------

    ingest_raw_data = PythonOperator(
        task_id="ingest_raw_data",
        python_callable=task_ingest,
        doc_md="Ingest raw CSV files from source and record audit metadata",
    )

    # --------------------------------------------------------
    # 3. Validation
    # --------------------------------------------------------

    validate_and_quarantine = PythonOperator(
        task_id="validate_and_quarantine",
        python_callable=task_validate,
        doc_md=(
            "Validate missing values, range 0-20, "
            "domain checks and quarantine rejected records"
        ),
    )

    # --------------------------------------------------------
    # 4. Transformation
    # --------------------------------------------------------

    transform_features = PythonOperator(
        task_id="transform_features",
        python_callable=task_transform,
        doc_md=(
            "Compute academic indicators: avg_grade, "
            "pass_fail, attendance_rate, risk_status"
        ),
    )

    # --------------------------------------------------------
    # 5. PostgreSQL Loading
    # --------------------------------------------------------

    load_postgresql_tables = PythonOperator(
        task_id="load_postgresql_tables",
        python_callable=task_load_postgres,
        doc_md=(
            "Load cleaned records into PostgreSQL "
            "dimensional and fact tables"
        ),
    )

    # --------------------------------------------------------
    # 6. Analytics Data Mart
    # --------------------------------------------------------

    build_analytics_mart = PythonOperator(
        task_id="build_analytics_mart",
        python_callable=task_build_analytics,
        doc_md=(
            "Generate and verify denormalized "
            "analytical table and views"
        ),
    )

    # --------------------------------------------------------
    # 7. Completion
    # --------------------------------------------------------

    pipeline_complete = EmptyOperator(
        task_id="pipeline_complete",
        doc_md="End marker indicating successful pipeline execution",
    )

    # --------------------------------------------------------
    # DAG Dependency Flow
    # --------------------------------------------------------

    (
        start_pipeline
        >> ingest_raw_data
        >> validate_and_quarantine
        >> transform_features
        >> load_postgresql_tables
        >> build_analytics_mart
        >> pipeline_complete
    )


# ============================================================
# Standalone Runner
# ============================================================

def run_standalone_pipeline():
    """
    Run the pipeline sequentially without Airflow.

    Useful for local testing of the pipeline functions.
    """

    print("=" * 70)
    print("EXECUTING STANDALONE PIPELINE WORKFLOW")
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


# ============================================================
# Local Python Execution
# ============================================================

if __name__ == "__main__":
    run_standalone_pipeline()