"""
Data Ingestion Module
---------------------
Responsible for extracting student performance datasets (Math & Portuguese),
recording extraction metadata/audit details, verifying file integrity, and
preserving pristine raw copies in data/raw/.
"""

import os
import sys
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ingestion")

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

# Reliable online sources for UCI Student Performance Dataset
DATASET_URLS = {
    "student-mat.csv": [
        "https://raw.githubusercontent.com/KunjalJethwani/StudentPerformance/main/student-mat.csv",
        "https://raw.githubusercontent.com/arunkumarramanan/student-performance/master/student-mat.csv"
    ],
    "student-por.csv": [
        "https://raw.githubusercontent.com/KunjalJethwani/StudentPerformance/main/student-por.csv",
        "https://raw.githubusercontent.com/arunkumarramanan/student-performance/master/student-por.csv"
    ]
}


def ensure_directories():
    """Ensure raw directory exists."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_dataset(filename: str, target_path: Path) -> bool:
    """Download dataset from remote source if not present locally."""
    urls = DATASET_URLS.get(filename, [])
    for url in urls:
        try:
            logger.info(f"Downloading {filename} from {url}...")
            response = requests.get(url, timeout=15)
            if response.status_code == 200 and len(response.content) > 1000:
                target_path.write_bytes(response.content)
                logger.info(f"Successfully downloaded and saved {filename} ({len(response.content)} bytes)")
                return True
        except Exception as e:
            logger.warning(f"Failed download from {url}: {e}")
    return False


def detect_delimiter(file_path: Path) -> str:
    """Detect whether file uses semicolon or comma as delimiter."""
    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline()
    if first_line.count(";") > first_line.count(","):
        return ";"
    return ","


def ingest_file(file_path: Path, source_name: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Ingest a single CSV file with audit metadata recording.
    
    Flow:
    1. Check file exists
    2. Read using Pandas with auto-detected delimiter
    3. Record extraction date, source, row count, column count
    4. Return loaded DataFrame and audit metadata dictionary
    """
    ensure_directories()
    
    if not file_path.exists():
        # Attempt download if filename matches known datasets
        filename = file_path.name
        if filename in DATASET_URLS:
            success = download_dataset(filename, file_path)
            if not success:
                raise FileNotFoundError(f"Source file {file_path} not found and download failed.")
        else:
            raise FileNotFoundError(f"Source file {file_path} not found.")

    extraction_date = datetime.datetime.now(datetime.timezone.utc).isoformat()
    delimiter = detect_delimiter(file_path)
    
    logger.info(f"Reading {file_path.name} with delimiter '{delimiter}'...")
    df = pd.read_csv(file_path, sep=delimiter)
    
    row_count, col_count = df.shape
    
    audit_metadata = {
        "source_file": file_path.name,
        "source_path": str(file_path.resolve()),
        "source_name": source_name or file_path.stem,
        "extraction_date": extraction_date,
        "row_count": row_count,
        "column_count": col_count,
        "columns": list(df.columns),
        "delimiter": delimiter,
        "status": "SUCCESS"
    }
    
    logger.info(f"Ingested {file_path.name}: {row_count} rows, {col_count} columns.")
    return df, audit_metadata


def ingest_all() -> Dict[str, Any]:
    """
    Ingest all available raw student datasets and record audit trail.
    Ensures pristine raw copies exist in data/raw/.
    """
    ensure_directories()
    results = {}
    audit_logs = []
    
    datasets = [
        ("student-mat.csv", "UCI Student Performance - Mathematics"),
        ("student-por.csv", "UCI Student Performance - Portuguese")
    ]
    
    for filename, source_name in datasets:
        target_path = RAW_DIR / filename
        df, audit_meta = ingest_file(target_path, source_name=source_name)
        results[filename] = df
        audit_logs.append(audit_meta)
    
    # Save audit log to data/raw/
    audit_path = RAW_DIR / "ingestion_audit.json"
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_logs, f, indent=2)
    logger.info(f"Saved ingestion audit log to {audit_path}")
    
    return {
        "datasets": results,
        "audit": audit_logs
    }


if __name__ == "__main__":
    logger.info("Starting Data Ingestion pipeline stage...")
    res = ingest_all()
    print("\n--- Ingestion Summary ---")
    for log in res["audit"]:
        print(f"Dataset: {log['source_name']} | Rows: {log['row_count']} | Cols: {log['column_count']} | Extracted At: {log['extraction_date']}")
    print("Ingestion completed successfully.\n")
