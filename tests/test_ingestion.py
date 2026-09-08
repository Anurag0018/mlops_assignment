"""
Unit Tests for Data Ingestion Module
"""

import os
from pathlib import Path
import pytest
import pandas as pd
from src.ingestion.ingest import detect_delimiter, ingest_file, RAW_DIR


def test_detect_delimiter(tmp_path):
    # Test semicolon delimiter
    file_semi = tmp_path / "semi.csv"
    file_semi.write_text("col1;col2;col3\n1;2;3", encoding="utf-8")
    assert detect_delimiter(file_semi) == ";"

    # Test comma delimiter
    file_comma = tmp_path / "comma.csv"
    file_comma.write_text("col1,col2,col3\n1,2,3", encoding="utf-8")
    assert detect_delimiter(file_comma) == ","


def test_ingest_file_missing_raises():
    missing_path = Path("data/raw/non_existent_file_xyz.csv")
    with pytest.raises(FileNotFoundError):
        ingest_file(missing_path)


def test_ingest_existing_raw_data():
    mat_path = RAW_DIR / "student-mat.csv"
    if not mat_path.exists():
        pytest.skip("student-mat.csv not downloaded yet")
        
    df, meta = ingest_file(mat_path, source_name="Test Math Ingestion")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert meta["status"] == "SUCCESS"
    assert meta["row_count"] == len(df)
    assert "extraction_date" in meta
    assert "columns" in meta
    assert "G1" in df.columns and "G2" in df.columns and "G3" in df.columns
