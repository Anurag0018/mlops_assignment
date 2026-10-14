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

try:
    from airflow.sdk import DAG
    from airflow.providers.standard.operators.python import PythonOperator
    from airflow.providers.standard.operators.empty import EmptyOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    try:
        from airflow import DAG
        from airflow.operators.python import PythonOperator
        from airflow.operators.empty import EmptyOperator
        AIRFLOW_AVAILABLE = True
    except ImportError:
        AIRFLOW_AVAILABLE = False
        class DAG:
            def __init__(self, *args, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
        class EmptyOperator:
            def __init__(self, *args, **kwargs): pass
            def __rshift__(self, other): return other
        class PythonOperator:
            def __init__(self, *args, **kwargs): pass
            def __rshift__(self, other): return other


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


def task_build_features(**context):
    from src.features.build_features import prepare_data_and_features
    res = prepare_data_and_features()
    print(f"Feature Engineering Task Completed: {res[0].shape[1]} transformed features across 3 stratified splits.")
    return {"transformed_features": int(res[0].shape[1]), "train_samples": int(len(res[3]))}


def task_train_models(**context):
    from src.training.train import run_training_pipeline
    registry = run_training_pipeline()
    print(f"MLflow Training Task Completed. Champion: {registry.get('champion_model_name')} ({registry.get('model_version')})")
    return registry


def task_drift_check(**context):
    import pandas as pd
    from src.monitoring.drift import DriftDetector
    from src.common.config import STUDENT_ANALYTICS_CSV
    df = pd.read_csv(STUDENT_ANALYTICS_CSV)
    detector = DriftDetector()
    report = detector.evaluate_drift(df)
    print(f"Feature Drift Monitoring Task Completed: Status = {report.get('overall_drift_status')}, Avg PSI = {report.get('average_psi', 0):.4f}")
    return report


# ============================================================
# Default Arguments
# ============================================================

default_args = {
    "owner": "mlops_engineering_team",
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
    description="End-to-end Student Performance Data & MLOps Pipeline",
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
    # 7. MLOps Feature Engineering Pipeline
    # --------------------------------------------------------

    build_feature_pipeline = PythonOperator(
        task_id="build_feature_pipeline",
        python_callable=task_build_features,
        doc_md="Fit leak-free ColumnTransformer and create stratified splits",
    )

    # --------------------------------------------------------
    # 8. Model Training & MLflow Tracking
    # --------------------------------------------------------

    train_and_track_models = PythonOperator(
        task_id="train_and_track_models",
        python_callable=task_train_models,
        doc_md="Benchmark Logistic Regression, RF, XGBoost and log to MLflow",
    )

    # --------------------------------------------------------
    # 9. Feature Drift Monitoring
    # --------------------------------------------------------

    monitor_feature_drift = PythonOperator(
        task_id="monitor_feature_drift",
        python_callable=task_drift_check,
        doc_md="Evaluate Population Stability Index (PSI) against baseline",
    )

    # --------------------------------------------------------
    # 10. Completion
    # --------------------------------------------------------

    pipeline_complete = EmptyOperator(
        task_id="pipeline_complete",
        doc_md="End marker indicating successful end-to-end pipeline execution",
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
        >> build_feature_pipeline
        >> train_and_track_models
        >> monitor_feature_drift
        >> pipeline_complete
    )


# ============================================================
# Standalone Runner
# ============================================================

def run_standalone_pipeline():
    """
    Run the complete 8-step pipeline sequentially without Airflow.
    Useful for local testing, CI/CD, and demonstrations.
    """

    print("=" * 70)
    print("EXECUTING COMPLETE DATA ENGINEERING & MLOPS PIPELINE WORKFLOW")
    print("=" * 70)

    print("\n[Step 1/8] Ingesting Raw Data...")
    task_ingest()

    print("\n[Step 2/8] Validating & Quarantining Records...")
    task_validate()

    print("\n[Step 3/8] Transforming & Engineering Academic Features...")
    task_transform()

    print("\n[Step 4/8] Loading into PostgreSQL / Relational Database...")
    task_load_postgres()

    print("\n[Step 5/8] Building & Verifying Analytics Data Mart...")
    task_build_analytics()

    print("\n[Step 6/8] Building Leak-Free Feature Pipelines & ColumnTransformers...")
    task_build_features()

    print("\n[Step 7/8] Benchmarking Models & Logging to MLflow...")
    task_train_models()

    print("\n[Step 8/8] Evaluating Feature Drift (PSI) & Quality Health...")
    task_drift_check()

    print("\n" + "=" * 70)
    print("COMPLETE END-TO-END PIPELINE EXECUTED SUCCESSFULLY!")
    print("=" * 70)


# ============================================================
# Local Python Execution
# ============================================================

if __name__ == "__main__":
    run_standalone_pipeline()