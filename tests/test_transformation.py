"""
Unit Tests for Data Transformation Module
"""

import pytest
import pandas as pd
from src.transformation.transform import (
    map_performance_category,
    calculate_risk_status,
    transform_staging_data
)


def test_map_performance_category():
    assert map_performance_category(18) == "Distinction"
    assert map_performance_category(16) == "Distinction"
    assert map_performance_category(15) == "Good"
    assert map_performance_category(14) == "Good"
    assert map_performance_category(12) == "Satisfactory"
    assert map_performance_category(10) == "Satisfactory"
    assert map_performance_category(9) == "At-Risk"
    assert map_performance_category(0) == "At-Risk"


def test_calculate_risk_status():
    # Low risk: good marks, 0 failures, low absences
    row_low = pd.Series({"g3": 14, "failures": 0, "absences": 2})
    assert calculate_risk_status(row_low) == "Low Risk"

    # Medium risk: failing marks but no other compounding factors
    row_med = pd.Series({"g3": 8, "failures": 0, "absences": 2})
    assert calculate_risk_status(row_med) == "Medium Risk"

    # High risk: failing marks AND past failures
    row_high = pd.Series({"g3": 6, "failures": 2, "absences": 12})
    assert calculate_risk_status(row_high) == "High Risk"


def test_transformation_pipeline_features(tmp_path):
    # Create sample staging CSV
    sample_data = {
        "school": ["GP", "MS"],
        "sex": ["F", "M"],
        "age": [17, 18],
        "address": ["U", "R"],
        "famsize": ["GT3", "LE3"],
        "pstatus": ["T", "A"],
        "medu": [4, 1],
        "fedu": [3, 2],
        "mjob": ["services", "other"],
        "fjob": ["teacher", "other"],
        "reason": ["course", "home"],
        "guardian": ["mother", "father"],
        "traveltime": [1, 2],
        "studytime": [3, 1],
        "failures": [0, 2],
        "schoolsup": ["no", "no"],
        "famsup": ["yes", "no"],
        "paid": ["no", "yes"],
        "activities": ["yes", "no"],
        "nursery": ["yes", "yes"],
        "higher": ["yes", "no"],
        "internet": ["yes", "no"],
        "romantic": ["no", "yes"],
        "famrel": [4, 3],
        "freetime": [3, 2],
        "goout": [2, 4],
        "dalc": [1, 2],
        "walc": [1, 3],
        "health": [5, 2],
        "absences": [4, 20],
        "g1": [12, 6],
        "g2": [14, 7],
        "g3": [16, 5],
        "subject": ["Mathematics", "Portuguese"],
        "student_id": ["STU-0001", "STU-0002"]
    }
    staging_file = tmp_path / "staging_sample.csv"
    pd.DataFrame(sample_data).to_csv(staging_file, index=False)

    df_students, df_academic, df_analytics = transform_staging_data(staging_file)

    # Verify dimensional tables
    assert len(df_students) == 2
    assert len(df_academic) == 2
    assert len(df_analytics) == 2

    # Verify calculated features on first record
    row1 = df_analytics.iloc[0]
    assert row1["average_grade"] == 14.0  # (12 + 14 + 16) / 3
    assert row1["final_grade"] == 16
    assert row1["pass_fail"] == "Pass"
    assert row1["performance_category"] == "Distinction"
    assert row1["grade_improvement"] == 4  # 16 - 12
    assert row1["study_time_category"] == "5 to 10 hours"
    assert row1["parent_education"] == "Higher Education"
    assert row1["risk_status"] == "Low Risk"

    # Verify calculated features on second record (At-Risk)
    row2 = df_analytics.iloc[1]
    assert row2["pass_fail"] == "Fail"
    assert row2["performance_category"] == "At-Risk"
    assert row2["risk_status"] == "High Risk"
