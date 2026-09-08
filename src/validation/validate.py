"""
Data Validation Module
----------------------
Validates raw student records against business rules:
- Null / Missing values
- Value ranges: G1, G2, G3 in [0, 20], age in [15, 25], absences >= 0
- Categorical domains: sex in {M, F}, school in {GP, MS}, address in {U, R}, etc.
- Duplicate student records within subject

Separates records into:
- Valid records -> data/staging/staging_students.csv
- Invalid records -> data/rejected/rejected_records.csv (with error reason & timestamp)
"""

import os
import sys
import hashlib
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("validation")

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
STAGING_DIR = BASE_DIR / "data" / "staging"
REJECTED_DIR = BASE_DIR / "data" / "rejected"

# Demographic columns that uniquely identify an individual student across subjects
STUDENT_KEY_COLS = [
    "school", "sex", "age", "address", "famsize", 
    "Pstatus", "Medu", "Fedu", "Mjob", "Fjob", 
    "reason", "nursery", "internet"
]


def ensure_directories():
    """Ensure staging and rejected directories exist."""
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)


def generate_student_id(row: pd.Series) -> str:
    """Generate a consistent deterministic student ID from key demographic features."""
    key_str = "|".join(str(row.get(col, "")).strip().lower() for col in STUDENT_KEY_COLS)
    h = hashlib.sha256(key_str.encode("utf-8")).hexdigest()[:8].upper()
    return f"STU-{h}"


def validate_record(row: pd.Series) -> List[str]:
    """
    Validate an individual record against all schema rules.
    Returns a list of violation error strings (empty if valid).
    """
    errors = []

    # 1. Check for NULL or NaN values
    null_cols = [c for c in row.index if pd.isna(row[c])]
    if null_cols:
        errors.append(f"Missing values in columns: {', '.join(null_cols)}")

    # 2. Check Grade Ranges (0 - 20)
    for g_col in ["G1", "G2", "G3"]:
        if g_col in row and pd.notna(row[g_col]):
            try:
                g_val = float(row[g_col])
                if g_val < 0 or g_val > 20:
                    errors.append(f"Invalid {g_col} mark '{g_val}': must be between 0 and 20")
            except (ValueError, TypeError):
                errors.append(f"Invalid non-numeric value for {g_col}: '{row[g_col]}'")

    # 3. Check Age (15 - 25)
    if "age" in row and pd.notna(row["age"]):
        try:
            age = int(row["age"])
            if age < 15 or age > 25:
                errors.append(f"Invalid age '{age}': must be between 15 and 25")
        except (ValueError, TypeError):
            errors.append(f"Invalid non-integer age: '{row['age']}'")

    # 4. Check Absences (>= 0)
    if "absences" in row and pd.notna(row["absences"]):
        try:
            absences = int(row["absences"])
            if absences < 0:
                errors.append(f"Invalid absences '{absences}': cannot be negative")
        except (ValueError, TypeError):
            errors.append(f"Invalid non-integer absences: '{row['absences']}'")

    # 5. Check Study Time (1 - 4)
    if "studytime" in row and pd.notna(row["studytime"]):
        try:
            st = int(row["studytime"])
            if st not in [1, 2, 3, 4]:
                errors.append(f"Invalid studytime '{st}': must be in {{1, 2, 3, 4}}")
        except (ValueError, TypeError):
            errors.append(f"Invalid non-integer studytime: '{row['studytime']}'")

    # 6. Check Failures (0 - 4)
    if "failures" in row and pd.notna(row["failures"]):
        try:
            f = int(row["failures"])
            if f < 0 or f > 4:
                errors.append(f"Invalid failures '{f}': must be between 0 and 4")
        except (ValueError, TypeError):
            errors.append(f"Invalid non-integer failures: '{row['failures']}'")

    # 7. Categorical Checks
    if "sex" in row and pd.notna(row["sex"]):
        if str(row["sex"]).strip().upper() not in ["M", "F"]:
            errors.append(f"Invalid gender '{row['sex']}': must be 'M' or 'F'")

    if "school" in row and pd.notna(row["school"]):
        if str(row["school"]).strip().upper() not in ["GP", "MS"]:
            errors.append(f"Invalid school '{row['school']}': must be 'GP' or 'MS'")

    if "address" in row and pd.notna(row["address"]):
        if str(row["address"]).strip().upper() not in ["U", "R"]:
            errors.append(f"Invalid address '{row['address']}': must be 'U' (Urban) or 'R' (Rural)")

    if "famsize" in row and pd.notna(row["famsize"]):
        if str(row["famsize"]).strip().upper() not in ["LE3", "GT3"]:
            errors.append(f"Invalid famsize '{row['famsize']}': must be 'LE3' or 'GT3'")

    if "Pstatus" in row and pd.notna(row["Pstatus"]):
        if str(row["Pstatus"]).strip().upper() not in ["T", "A"]:
            errors.append(f"Invalid Pstatus '{row['Pstatus']}': must be 'T' (Together) or 'A' (Apart)")

    return errors


def validate_dataframe(df: pd.DataFrame, subject: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate an entire DataFrame of student records for a subject.
    Detects record-level validation failures as well as duplicates within the subject.
    Returns (valid_df, rejected_df).
    """
    df = df.copy()
    df["subject"] = subject
    
    # Generate deterministic student_id
    df["student_id"] = df.apply(generate_student_id, axis=1)

    rejected_records = []
    valid_indices = []

    # Check duplicates within the same subject
    duplicate_mask = df.duplicated(subset=["student_id", "subject"], keep="first")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for idx, row in df.iterrows():
        errors = []

        # Duplicate check
        if duplicate_mask.loc[idx]:
            errors.append(f"Duplicate student record for subject '{subject}'")

        # Field-level validation checks
        field_errors = validate_record(row)
        errors.extend(field_errors)

        if errors:
            rej_dict = row.to_dict()
            rej_dict["rejection_reason"] = " | ".join(errors)
            rej_dict["rejected_at"] = now_iso
            rejected_records.append(rej_dict)
        else:
            valid_indices.append(idx)

    valid_df = df.loc[valid_indices].copy()
    rejected_df = pd.DataFrame(rejected_records)

    return valid_df, rejected_df


def run_validation(inject_synthetic_errors: bool = False) -> Dict[str, Any]:
    """
    Execute full validation on raw student datasets.
    Routes clean records to data/staging/staging_students.csv
    Routes invalid records to data/rejected/rejected_records.csv
    """
    ensure_directories()
    
    mat_path = RAW_DIR / "student-mat.csv"
    por_path = RAW_DIR / "student-por.csv"
    
    if not mat_path.exists() or not por_path.exists():
        logger.warning("Raw files missing. Triggering ingestion first...")
        from src.ingestion.ingest import ingest_all
        ingest_all()

    # Load raw files
    df_mat = pd.read_csv(mat_path, sep=";" if ";" in open(mat_path).readline() else ",")
    df_por = pd.read_csv(por_path, sep=";" if ";" in open(por_path).readline() else ",")

    # Optionally inject synthetic errors for demonstration/testing if requested
    if inject_synthetic_errors:
        logger.info("Injecting demonstration synthetic edge cases (negative grade, invalid sex)...")
        bad_row1 = df_mat.iloc[0].copy()
        bad_row1["G1"] = -5  # Invalid negative mark
        bad_row2 = df_mat.iloc[1].copy()
        bad_row2["sex"] = "X"  # Invalid gender
        df_mat = pd.concat([df_mat, pd.DataFrame([bad_row1, bad_row2])], ignore_index=True)

    # Validate each subject
    valid_mat, rej_mat = validate_dataframe(df_mat, subject="Mathematics")
    valid_por, rej_por = validate_dataframe(df_por, subject="Portuguese")

    # Combine valid records
    staging_df = pd.concat([valid_mat, valid_por], ignore_index=True)
    staging_path = STAGING_DIR / "staging_students.csv"
    staging_df.to_csv(staging_path, index=False)
    logger.info(f"Saved {len(staging_df)} validated records to staging: {staging_path}")

    # Combine rejected records
    rejected_dfs = [df for df in [rej_mat, rej_por] if not df.empty]
    rejected_path = REJECTED_DIR / "rejected_records.csv"
    if rejected_dfs:
        combined_rej = pd.concat(rejected_dfs, ignore_index=True)
        combined_rej.to_csv(rejected_path, index=False)
        logger.warning(f"Quarantined {len(combined_rej)} rejected records to: {rejected_path}")
    else:
        # Create empty rejected file with appropriate schema headers
        empty_rej = pd.DataFrame(columns=list(df_mat.columns) + ["subject", "student_id", "rejection_reason", "rejected_at"])
        empty_rej.to_csv(rejected_path, index=False)
        logger.info(f"No validation errors found in raw data. Created clean log at: {rejected_path}")
        combined_rej = empty_rej

    summary = {
        "math_total": len(df_mat),
        "math_valid": len(valid_mat),
        "math_rejected": len(rej_mat),
        "por_total": len(df_por),
        "por_valid": len(valid_por),
        "por_rejected": len(rej_por),
        "total_staging": len(staging_df),
        "total_rejected": len(combined_rej)
    }

    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate Student Performance raw records")
    parser.add_argument("--inject-errors", action="store_true", help="Inject sample invalid rows to demonstrate rejection")
    args = parser.parse_args()

    logger.info("Starting Data Validation pipeline stage...")
    stats = run_validation(inject_synthetic_errors=args.inject_errors)
    print("\n--- Validation Summary ---")
    for k, v in stats.items():
        print(f"{k}: {v}")
    print("Validation completed successfully.\n")
