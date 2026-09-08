"""
Unit Tests for Data Validation Module
"""

import pytest
import pandas as pd
from src.validation.validate import validate_record, validate_dataframe, generate_student_id


@pytest.fixture
def sample_valid_row():
    return pd.Series({
        "school": "GP",
        "sex": "F",
        "age": 17,
        "address": "U",
        "famsize": "GT3",
        "Pstatus": "T",
        "Medu": 3,
        "Fedu": 2,
        "Mjob": "services",
        "Fjob": "other",
        "reason": "course",
        "guardian": "mother",
        "traveltime": 1,
        "studytime": 2,
        "failures": 0,
        "schoolsup": "no",
        "famsup": "yes",
        "paid": "no",
        "activities": "yes",
        "nursery": "yes",
        "higher": "yes",
        "internet": "yes",
        "romantic": "no",
        "famrel": 4,
        "freetime": 3,
        "goout": 3,
        "Dalc": 1,
        "Walc": 2,
        "health": 4,
        "absences": 4,
        "G1": 12,
        "G2": 14,
        "G3": 15
    })


def test_valid_row_passes(sample_valid_row):
    errors = validate_record(sample_valid_row)
    assert errors == []


def test_invalid_grade_range(sample_valid_row):
    # Grade below 0
    row_low = sample_valid_row.copy()
    row_low["G1"] = -5
    errors = validate_record(row_low)
    assert any("Invalid G1 mark" in e for e in errors)

    # Grade above 20
    row_high = sample_valid_row.copy()
    row_high["G3"] = 25
    errors = validate_record(row_high)
    assert any("Invalid G3 mark" in e for e in errors)


def test_invalid_categorical_values(sample_valid_row):
    # Invalid gender
    row_gender = sample_valid_row.copy()
    row_gender["sex"] = "Z"
    errors = validate_record(row_gender)
    assert any("Invalid gender" in e for e in errors)

    # Invalid school
    row_school = sample_valid_row.copy()
    row_school["school"] = "XYZ"
    errors = validate_record(row_school)
    assert any("Invalid school" in e for e in errors)


def test_negative_absences(sample_valid_row):
    row_abs = sample_valid_row.copy()
    row_abs["absences"] = -3
    errors = validate_record(row_abs)
    assert any("Invalid absences" in e for e in errors)


def test_missing_values(sample_valid_row):
    row_null = sample_valid_row.copy()
    row_null["age"] = None
    errors = validate_record(row_null)
    assert any("Missing values" in e for e in errors)


def test_validate_dataframe_quarantine(sample_valid_row):
    valid_record = sample_valid_row.to_dict()
    
    corrupt_record = sample_valid_row.to_dict()
    corrupt_record["G2"] = -10  # corrupted mark

    df = pd.DataFrame([valid_record, corrupt_record])
    valid_df, rej_df = validate_dataframe(df, subject="Mathematics")

    assert len(valid_df) == 1
    assert len(rej_df) == 1
    assert "rejection_reason" in rej_df.columns
    assert "rejected_at" in rej_df.columns
    assert "Invalid G2 mark" in rej_df.iloc[0]["rejection_reason"]


def test_duplicate_student_quarantine(sample_valid_row):
    rec1 = sample_valid_row.to_dict()
    rec2 = sample_valid_row.to_dict()  # exact duplicate in same subject

    df = pd.DataFrame([rec1, rec2])
    valid_df, rej_df = validate_dataframe(df, subject="Mathematics")

    assert len(valid_df) == 1
    assert len(rej_df) == 1
    assert "Duplicate student record" in rej_df.iloc[0]["rejection_reason"]
