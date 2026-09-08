"""
Data Transformation Module
--------------------------
Transforms staging data into normalized cleaned relational datasets and an
analytical data mart with engineered academic indicators:
- average_grade: (G1 + G2 + G3) / 3
- final_grade: G3
- pass_fail: 'Pass' (G3 >= 10) vs 'Fail' (G3 < 10)
- performance_category: 'Distinction', 'Good', 'Satisfactory', 'At-Risk'
- attendance_rate: 100 * (1 - absences / 93)
- study_time_category: readable weekly study buckets
- parent_education: max parental education tier
- grade_improvement: G3 - G1 trend
- risk_status: 'High Risk', 'Medium Risk', 'Low Risk'

Outputs saved to data/cleaned/:
1. students.csv (Demographic Dimension)
2. academic_performance.csv (Course & Habits Fact)
3. student_analytics.csv (Denormalized Data Mart)
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("transformation")

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "data" / "staging"
CLEANED_DIR = BASE_DIR / "data" / "cleaned"

# Max absences in the dataset for attendance percentage baseline
MAX_SESSION_ABSENCES = 93

# Educational level mappings
EDU_MAP = {
    0: "None",
    1: "Primary (4th grade)",
    2: "5th to 9th grade",
    3: "Secondary Education",
    4: "Higher Education"
}

# Study time category mappings
STUDY_TIME_MAP = {
    1: "<2 hours",
    2: "2 to 5 hours",
    3: "5 to 10 hours",
    4: ">10 hours"
}


def ensure_directories():
    """Ensure cleaned directory exists."""
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)


def map_performance_category(g3: float) -> str:
    """Classify Portuguese scale final grade (0-20)."""
    if g3 >= 16:
        return "Distinction"
    elif g3 >= 14:
        return "Good"
    elif g3 >= 10:
        return "Satisfactory"
    else:
        return "At-Risk"


def calculate_risk_status(row: pd.Series) -> str:
    """Classify academic risk based on marks, failures, and attendance."""
    is_failing = row["g3"] < 10
    has_failures = row["failures"] > 0
    high_absences = row["absences"] > 10

    if is_failing and (has_failures or high_absences):
        return "High Risk"
    elif is_failing or has_failures or high_absences:
        return "Medium Risk"
    else:
        return "Low Risk"


def transform_staging_data(staging_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load staging data, engineer academic features, and split into relational tables:
    - students
    - academic_performance
    - student_analytics (mart)
    """
    ensure_directories()
    
    if not staging_path.exists():
        raise FileNotFoundError(f"Staging file not found at {staging_path}. Run validation first.")

    df = pd.read_csv(staging_path)
    # Standardize all column names to lowercase
    df.columns = [c.lower() for c in df.columns]
    logger.info(f"Loaded {len(df)} staging records for transformation.")

    # 1. Feature Engineering
    # Grade metrics
    df["average_grade"] = ((df["g1"] + df["g2"] + df["g3"]) / 3.0).round(2)
    df["final_grade"] = df["g3"].astype(int)
    df["pass_fail"] = np.where(df["final_grade"] >= 10, "Pass", "Fail")
    df["performance_category"] = df["final_grade"].apply(map_performance_category)
    df["grade_improvement"] = (df["g3"] - df["g1"]).astype(int)

    # Attendance metrics
    df["attendance_rate"] = (
        np.maximum(0.0, 1.0 - (df["absences"] / float(MAX_SESSION_ABSENCES))) * 100.0
    ).round(2)

    # Study habits & parent education
    df["study_time_category"] = df["studytime"].map(STUDY_TIME_MAP).fillna("Unknown")
    
    max_parent_edu = df[["medu", "fedu"]].max(axis=1)
    df["parent_education"] = max_parent_edu.map(EDU_MAP).fillna("Unknown")

    # Risk status indicator
    df["risk_status"] = df.apply(calculate_risk_status, axis=1)

    # 2. Extract Relational Dimensions & Facts

    # Table 1: Students Dimension (1 record per unique student)
    student_cols = [
        "student_id", "school", "sex", "age", "address", 
        "famsize", "pstatus", "medu", "fedu", "mjob", 
        "fjob", "reason", "guardian", "parent_education"
    ]
    df_students = df[student_cols].drop_duplicates(subset=["student_id"]).reset_index(drop=True)

    # Table 2: Academic Performance Fact (Course-level details)
    academic_cols = [
        "student_id", "subject", "studytime", "study_time_category", 
        "failures", "schoolsup", "famsup", "paid", "activities", 
        "nursery", "higher", "internet", "romantic", "famrel", 
        "freetime", "goout", "dalc", "walc", "health", "absences", 
        "attendance_rate", "g1", "g2", "g3"
    ]
    df_academic = df[academic_cols].drop_duplicates(subset=["student_id", "subject"]).reset_index(drop=True)

    # Table 3: Analytical Mart (Denormalized reporting table)
    analytics_cols = [
        "student_id", "school", "sex", "age", "address", "famsize", 
        "pstatus", "parent_education", "mjob", "fjob", "subject", 
        "studytime", "study_time_category", "failures", "absences", 
        "attendance_rate", "g1", "g2", "g3", "average_grade", 
        "final_grade", "pass_fail", "performance_category", 
        "grade_improvement", "risk_status"
    ]
    df_analytics = df[analytics_cols].copy()

    # 3. Save to Cleaned Layer
    students_file = CLEANED_DIR / "students.csv"
    academic_file = CLEANED_DIR / "academic_performance.csv"
    analytics_file = CLEANED_DIR / "student_analytics.csv"

    df_students.to_csv(students_file, index=False)
    df_academic.to_csv(academic_file, index=False)
    df_analytics.to_csv(analytics_file, index=False)

    logger.info(f"Saved {len(df_students)} students to {students_file}")
    logger.info(f"Saved {len(df_academic)} academic records to {academic_file}")
    logger.info(f"Saved {len(df_analytics)} analytical records to {analytics_file}")

    return df_students, df_academic, df_analytics


def run_transformation() -> Dict[str, Any]:
    """Execute complete transformation stage."""
    ensure_directories()
    staging_path = STAGING_DIR / "staging_students.csv"
    
    if not staging_path.exists():
        logger.warning("Staging data missing. Triggering validation first...")
        from src.validation.validate import run_validation
        run_validation()

    df_students, df_academic, df_analytics = transform_staging_data(staging_path)

    summary = {
        "unique_students": len(df_students),
        "total_academic_records": len(df_academic),
        "total_analytics_records": len(df_analytics),
        "overall_avg_grade": float(df_analytics["average_grade"].mean().round(2)),
        "pass_rate_pct": float(((df_analytics["pass_fail"] == "Pass").mean() * 100).round(2)),
        "high_risk_count": int((df_analytics["risk_status"] == "High Risk").sum())
    }

    return summary


if __name__ == "__main__":
    logger.info("Starting Data Transformation pipeline stage...")
    stats = run_transformation()
    print("\n--- Transformation Summary ---")
    for k, v in stats.items():
        print(f"{k}: {v}")
    print("Transformation completed successfully.\n")
