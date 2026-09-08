"""
Database Loading Module
-----------------------
Loads cleaned student dimensions, course facts, and analytical data mart into
relational storage (PostgreSQL). Provides seamless fallback to local SQLite
when PostgreSQL is offline for zero-dependency local testing.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("database")

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLEANED_DIR = BASE_DIR / "data" / "cleaned"
SQL_DIR = BASE_DIR / "sql"
SQLITE_DB_PATH = BASE_DIR / "data" / "student_performance.db"

# Database Configuration
DEFAULT_PG_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/student_db")
FALLBACK_SQLITE_URL = f"sqlite:///{SQLITE_DB_PATH.as_posix()}"


import socket


def is_postgres_online(host: str = "localhost", port: int = 5432) -> bool:
    """Probe if PostgreSQL port is open with minimal latency."""
    try:
        with socket.create_connection((host, int(port)), timeout=0.5):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def get_db_engine() -> Tuple[Engine, bool]:
    """
    Connect to PostgreSQL if reachable, otherwise fall back to SQLite.
    Returns (engine, is_postgres_flag).
    """
    pg_url = os.getenv("DATABASE_URL", DEFAULT_PG_URL)
    
    # Check if host and port are reachable before attempting full client connection
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", 5432))
    
    if is_postgres_online(host, port):
        try:
            engine = create_engine(pg_url, connect_args={"connect_timeout": 3})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Connected successfully to PostgreSQL database: {host}:{port}")
            return engine, True
        except Exception as e:
            logger.warning(f"PostgreSQL probe succeeded but connection failed: {e}")

    # Seamless fallback to embedded SQLite
    logger.info(f"PostgreSQL server not detected on {host}:{port}. Active storage: local SQLite ({SQLITE_DB_PATH.name})")
    sqlite_engine = create_engine(FALLBACK_SQLITE_URL)
    return sqlite_engine, False



def execute_sql_file(engine: Engine, sql_path: Path, is_postgres: bool):
    """Execute DDL/DML script with database dialect awareness."""
    if not sql_path.exists():
        logger.warning(f"SQL file {sql_path} does not exist. Skipping.")
        return

    sql_content = sql_path.read_text(encoding="utf-8")
    
    with engine.begin() as conn:
        if is_postgres:
            # PostgreSQL can execute multi-statement scripts directly
            conn.execute(text(sql_content))
        else:
            # SQLite compatibility: clean up PostgreSQL-specific syntax
            cleaned_sql = sql_content.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
            cleaned_sql = cleaned_sql.replace("CASCADE", "")
            cleaned_sql = cleaned_sql.replace("::NUMERIC", "")
            
            statements = [s.strip() for s in cleaned_sql.split(";") if s.strip()]
            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                except Exception as ex:
                    # Ignore view drops or subtle SQLite syntax differences
                    logger.debug(f"SQLite statement notice: {ex}")


def load_tables(engine: Engine) -> Dict[str, int]:
    """
    Load cleaned CSV files into relational tables:
    1. students
    2. academic_performance
    3. student_analytics
    """
    files_to_load = [
        ("students", CLEANED_DIR / "students.csv"),
        ("academic_performance", CLEANED_DIR / "academic_performance.csv"),
        ("student_analytics", CLEANED_DIR / "student_analytics.csv")
    ]

    counts = {}

    for table_name, file_path in files_to_load:
        if not file_path.exists():
            raise FileNotFoundError(f"Required cleaned file missing: {file_path}. Run transformation first.")

        df = pd.read_csv(file_path)
        
        # Write DataFrame into table (replace ensures idempotent loads)
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists="replace",
            index=False,
            chunksize=500
        )
        counts[table_name] = len(df)
        logger.info(f"Loaded {len(df)} rows into table '{table_name}'.")

    return counts


def run_database_load() -> Dict[str, Any]:
    """Execute complete database loading stage."""
    # Ensure cleaned data exists
    if not (CLEANED_DIR / "student_analytics.csv").exists():
        logger.warning("Cleaned data missing. Triggering transformation first...")
        from src.transformation.transform import run_transformation
        run_transformation()

    engine, is_postgres = get_db_engine()

    # Apply schema scripts
    schema_file = SQL_DIR / "schema.sql"
    analytics_file = SQL_DIR / "analytics.sql"

    logger.info("Initializing database schema...")
    try:
        execute_sql_file(engine, schema_file, is_postgres)
    except Exception as e:
        logger.warning(f"Notice executing schema.sql: {e}")

    logger.info("Loading cleaned datasets into database...")
    row_counts = load_tables(engine)

    logger.info("Initializing analytics views and marts...")
    try:
        execute_sql_file(engine, analytics_file, is_postgres)
    except Exception as e:
        logger.warning(f"Notice executing analytics.sql: {e}")

    summary = {
        "database_type": "PostgreSQL" if is_postgres else "SQLite (Fallback)",
        "tables_loaded": row_counts,
        "status": "SUCCESS"
    }

    return summary


def query_analytics_data() -> pd.DataFrame:
    """
    Helper function used by Streamlit Dashboard or analytics scripts
    to pull the latest analytical data mart.
    """
    engine, _ = get_db_engine()
    try:
        return pd.read_sql("SELECT * FROM student_analytics", con=engine)
    except Exception:
        # If DB query fails, read directly from cleaned CSV
        csv_path = CLEANED_DIR / "student_analytics.csv"
        return pd.read_csv(csv_path)


if __name__ == "__main__":
    logger.info("Starting Database Loading pipeline stage...")
    stats = run_database_load()
    print("\n--- Database Loading Summary ---")
    for k, v in stats.items():
        print(f"{k}: {v}")
    print("Database loading completed successfully.\n")
