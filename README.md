# Student Performance Data Engineering Pipeline (Part 1 — 50 Marks)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20%2F%20SQLite-informational.svg)](https://www.postgresql.org/)
[![Apache Airflow](https://img.shields.io/badge/Orchestration-Apache%20Airflow-red.svg)](https://airflow.apache.org/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Tests Passed](https://img.shields.io/badge/Pytest-13%2F13%20Passed-brightgreen.svg)](tests/)

An end-to-end, production-grade data engineering pipeline built for **Part 1** of the MLOps coursework. This project extracts, validates, quarantines, transforms, stores, and visualizes student academic performance data from the **UCI Student Performance Dataset** using Python, Pandas, PostgreSQL, Apache Airflow, and Streamlit.

---

## ⚡ Quick Launch (3-Second Startup)

Choose your preferred way to start the pipeline and dashboard:

### 1. One-Click Launchers (Windows)
- **Launch Dashboard**: Double-click `run_dashboard.bat` (or run `.\run_dashboard.ps1` in PowerShell).
- **Run Pipeline**: Double-click `run_pipeline.bat` (or run `.\run_pipeline.ps1` in PowerShell).

### 2. Command Line (Universal)
```powershell
# Run the complete 5-stage ETL pipeline
python dags/student_pipeline.py

# Launch the Streamlit dashboard on http://localhost:8501
python -m streamlit run dashboard/app.py

# Run all 13 automated tests
python -m pytest tests/ -v
```

---

## 1. Project Overview

Educational institutions require robust, reproducible data pipelines to identify at-risk students, track academic progression across evaluation periods, and monitor the correlation between attendance, study habits, and exam scores. 

This repository implements a complete automated pipeline:
- **Raw Data Ingestion**: Python & Pandas extraction with delimiter auto-detection and extraction audit logging.
- **Strict Data Validation & Quarantine**: Automated checks for missing values, range bounds ($0 \le G \le 20$), domain categoricals, and duplicate student records quarantined to `data/rejected/rejected_records.csv`.
- **Transformation & Feature Engineering**: Derived academic metrics (`average_grade`, `pass_fail`, `performance_category`, `attendance_rate`, `grade_improvement`, `risk_status`).
- **Relational PostgreSQL Storage & Data Mart**: Normalized star/dimensional tables (`students`, `academic_performance`) and analytical mart (`student_analytics`) with zero-config local SQLite fallback.
- **Workflow Orchestration**: Apache Airflow DAG (`student_data_pipeline`) orchestrating tasks with retries and dependency management.
- **Interactive Decision-Support Dashboard**: 5 rich Streamlit views covering overall KPIs, attendance impact, subject comparisons, demographic analysis, and individual student risk drill-downs.

---

## 2. Objectives & Marking Breakdown (50 Marks)

| Pipeline Component | Scope & Requirements | Marks | Status |
|---|---|---|---|
| **Data Ingestion & Raw Layer** | Python/Pandas extraction from raw CSVs, metadata tracking, pristine raw layer preservation | **10 Marks** | ✅ Completed |
| **Validation & Staging Layer** | Range checks (0–20), domain sets, missing values, duplicate detection, quarantine log | **10 Marks** | ✅ Completed |
| **Transformation & Feature Eng.** | Academic indicators (`avg_grade`, `pass_fail`, `attendance_rate`, `risk_status`), relational normalization | **10 Marks** | ✅ Completed |
| **PostgreSQL Database & Mart** | PostgreSQL relational schema (`sql/schema.sql`), analytical mart (`sql/analytics.sql`), automated loader | **10 Marks** | ✅ Completed |
| **Dashboard & Orchestration** | 5-view Streamlit dashboard, Apache Airflow DAG (`dags/student_pipeline.py`), documentation & unit tests | **10 Marks** | ✅ Completed |
| **Total** | **End-to-End Data Engineering Pipeline** | **50 Marks** | **100% Ready** |

---

## 3. Dataset Information

The pipeline uses the official **UCI Machine Learning Repository Student Performance Dataset** (Cortez and Silva, 2008).

- **Primary Source**: [UCI Student Performance Data Set](https://archive.ics.uci.edu/dataset/320/student+performance)
- **Course Subjects**:
  1. `student-mat.csv`: Mathematics course (395 records, 33 attributes)
  2. `student-por.csv`: Portuguese language course (649 records, 33 attributes)
- **Combined Volume**: 1,044 raw records (with 382 students enrolled in both courses).
- **Delimiter**: Semicolon (`;`) auto-detected during ingestion.
- **Core Attributes**:
  - **Demographic**: School (`GP`, `MS`), Sex (`F`, `M`), Age (15–22), Address (`U`, `R`), Family Size (`LE3`, `GT3`), Cohabitation Status (`T`, `A`).
  - **Family Background**: Mother's/Father's Education (`Medu`, `Fedu`: 0–4), Mother's/Father's Job (`Mjob`, `Fjob`).
  - **Academic Habits**: Study Time (1–4), Past Failures (0–4), Extra Support (`schoolsup`, `famsup`), Absences (0–93).
  - **Period Marks**: Period 1 (`G1`), Period 2 (`G2`), Final Grade (`G3`) on a 0–20 point scale.

*See [docs/data_dictionary.md](docs/data_dictionary.md) for full attribute definitions and constraints.*

---

## 4. Pipeline Architecture

![Architecture Diagram](docs/architecture.svg)

### Data Flow Diagram

```mermaid
flowchart TD
    subgraph Data Sources
        S1["student-mat.csv (Mathematics)"]
        S2["student-por.csv (Portuguese)"]
    end

    subgraph Data Ingestion
        ING["src/ingestion/ingest.py<br/>(Delimiter detection, metadata audit)"]
    end

    subgraph Raw Layer
        RAW["data/raw/<br/>(Immutable pristine copies)"]
    end

    subgraph Validation Engine
        VAL["src/validation/validate.py<br/>(Bounds 0-20, domain sets, nulls, duplicates)"]
        REJ["data/rejected/rejected_records.csv<br/>(Quarantined records + rejection reason)"]
    end

    subgraph Staging Layer
        STG["data/staging/staging_students.csv<br/>(1,028 Validated Records)"]
    end

    subgraph Transformation Engine
        TRF["src/transformation/transform.py<br/>(Features: avg_grade, pass_fail, perf_tier, attendance_rate)"]
    end

    subgraph Cleaned & Relational Layer
        CLN["data/cleaned/<br/>- students.csv (662 unique)<br/>- academic_performance.csv (1,028 facts)"]
        PG[("PostgreSQL Database<br/>- students<br/>- academic_performance<br/>- student_analytics (Data Mart)")]
    end

    subgraph Orchestration
        DAG["Airflow DAG: student_data_pipeline<br/>(ingest -> validate -> transform -> load_db -> build_mart)"]
    end

    subgraph Decision Support Dashboard
        DASH["Streamlit Dashboard (dashboard/app.py)<br/>1. Overall KPIs & Distributions<br/>2. Attendance vs Marks Correlation<br/>3. Subject Trends (Math vs Portuguese)<br/>4. Demographic Success Factors<br/>5. Student Profile & Risk Analyzer"]
    end

    S1 --> ING
    S2 --> ING
    ING --> RAW
    RAW --> VAL
    VAL -->|Violations| REJ
    VAL -->|Valid| STG
    STG --> TRF
    TRF --> CLN
    CLN --> PG
    DAG -. orchestrates .-> ING
    DAG -. orchestrates .-> VAL
    DAG -. orchestrates .-> TRF
    DAG -. orchestrates .-> PG
    PG --> DASH
```

---

## 5. Project Directory Structure

```
mlops_project/
├── data/
│   ├── raw/                           # Pristine raw CSV files & ingestion audit
│   │   ├── student-mat.csv
│   │   ├── student-por.csv
│   │   └── ingestion_audit.json
│   ├── staging/                       # Validated records before feature engineering
│   │   └── staging_students.csv       # (1,028 valid rows)
│   ├── cleaned/                       # Normalized relational datasets & data mart
│   │   ├── students.csv               # (662 unique student profiles)
│   │   ├── academic_performance.csv   # (1,028 course facts)
│   │   └── student_analytics.csv      # (1,028 analytical data mart rows)
│   ├── rejected/                      # Quarantined invalid & duplicate records
│   │   └── rejected_records.csv       # (16 duplicates with reason & timestamp)
│   └── student_performance.db         # Embedded SQLite database (Zero-config fallback)
│
├── src/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── ingest.py                  # Ingestion engine & audit metadata logger
│   ├── validation/
│   │   ├── __init__.py
│   │   └── validate.py                # Validation rules & quarantine logic
│   ├── transformation/
│   │   ├── __init__.py
│   │   └── transform.py               # Feature engineering & dimensional splitting
│   └── database/
│       ├── __init__.py
│       └── load.py                    # PostgreSQL / SQLite loader & query interface
│
├── dags/
│   └── student_pipeline.py            # Apache Airflow DAG & standalone CLI workflow
│
├── sql/
│   ├── schema.sql                     # PostgreSQL DDL for relational schema
│   └── analytics.sql                  # Analytical data mart & reporting views
│
├── dashboard/
│   └── app.py                         # 5-View interactive Streamlit dashboard
│
├── tests/
│   ├── test_ingestion.py              # Ingestion unit tests
│   ├── test_validation.py             # Validation & quarantining unit tests
│   └── test_transformation.py         # Feature engineering unit tests
│
├── docs/
│   ├── architecture.svg               # Vector architecture flowchart
│   ├── data_dictionary.md             # Comprehensive schema & column descriptions
│   └── validation_rules.md            # Data quality rules & rejection criteria
│
├── run_dashboard.bat                  # One-click Windows batch launcher for dashboard
├── run_dashboard.ps1                  # PowerShell launcher for dashboard
├── run_pipeline.bat                   # One-click Windows batch launcher for ETL pipeline
├── run_pipeline.ps1                   # PowerShell launcher for ETL pipeline
├── Dockerfile                         # Container definition for Streamlit app
├── docker-compose.yml                 # Multi-container PostgreSQL + Dashboard setup
├── requirements.txt                   # Project dependencies
├── .env.example                       # Environment configuration template
├── .gitignore                         # Git exclusion rules
└── README.md                          # Comprehensive project documentation
```

---

## 6. Technologies Used

- **Programming Language**: Python 3.12
- **Data Engineering & Manipulation**: Pandas 3.0, NumPy 1.26
- **Database & Storage**: PostgreSQL 15, SQLAlchemy 2.0, Psycopg2-binary, SQLite 3 (Automatic Fallback)
- **Workflow Orchestration**: Apache Airflow DAG (`PythonOperator`, `EmptyOperator`)
- **Data Visualization**: Streamlit 1.63, Plotly Express & Graph Objects 7.0, Statsmodels 0.15
- **Unit Testing**: Pytest 9.1
- **Containerization**: Docker, Docker Compose

---

## 7. Installation & Environment Setup

### Prerequisites
- Python 3.10+ installed
- Windows PowerShell / Linux terminal
- *(Optional)* Docker Desktop for PostgreSQL containerization

### Step 1: Clone Repository
```powershell
git clone <repository_url>
cd mlops_project
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure Environment
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Default `.env` configuration:
```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/student_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=student_db
DB_USER=postgres
DB_PASSWORD=postgres
```

> **Zero-Configuration Fallback:** If PostgreSQL is offline, the pipeline automatically detects it and switches to an embedded SQLite database at `data/student_performance.db` without crashing or throwing connection errors.

---

## 8. Database Architecture & Setup

### Relational Schema Design (`sql/schema.sql`)
- **`students` (Dimension)**: Stores demographic and family attributes keyed by deterministic `student_id`.
- **`academic_performance` (Fact)**: Stores course-level records, study habits, absences, and period marks (`g1`, `g2`, `g3`) linked via foreign key to `students.student_id`.
- **`ingestion_audit` (Audit)**: Records timestamps, row counts, and source file metadata.

### Analytical Data Mart (`sql/analytics.sql`)
- **`student_analytics` (OLAP Mart)**: Denormalized table optimized for analytics with derived metrics (`average_grade`, `final_grade`, `pass_fail`, `performance_category`, `grade_improvement`, `risk_status`).
- **Views**:
  - `vw_overall_kpis`: Institutional aggregate performance indicators.
  - `vw_subject_summary`: Math vs Portuguese comparative metrics.
  - `vw_attendance_impact`: Performance aggregated across absence tiers.
  - `vw_demographic_performance`: Performance by gender, location, and parental education.
  - `vw_at_risk_students`: Directory of students requiring educational intervention.

### Running PostgreSQL Container
To boot an isolated PostgreSQL instance:
```powershell
docker compose up -d postgres
```

---

## 9. Pipeline Execution

### Method 1: One-Click Execution (Windows)
Double-click **`run_pipeline.bat`** or run:
```powershell
.\run_pipeline.ps1
```

### Method 2: Command-Line Execution
```powershell
python dags/student_pipeline.py
```

### Step-by-Step Stage Execution:
1. **Ingestion**: `python src/ingestion/ingest.py`
2. **Validation**: `python src/validation/validate.py` *(use `--inject-errors` to test synthetic corruptions)*
3. **Transformation**: `python src/transformation/transform.py`
4. **Database Load**: `python src/database/load.py`

---

## 10. Apache Airflow Orchestration

The Airflow DAG is defined in [`dags/student_pipeline.py`](dags/student_pipeline.py) with the following dependency sequence:

```
[start_pipeline]
       │
       ▼
[ingest_raw_data]
       │
       ▼
[validate_and_quarantine]
       │
       ▼
[transform_features]
       │
       ▼
[load_postgresql_tables]
       │
       ▼
[build_analytics_mart]
       │
       ▼
[pipeline_complete]
```

### Deploying to Airflow:
1. Copy or symlink `dags/student_pipeline.py` into your Airflow `$AIRFLOW_HOME/dags/` folder.
2. Trigger the DAG:
   ```bash
   airflow dags trigger student_data_pipeline
   ```

---

## 11. Streamlit Interactive Dashboard (5 Views)

### Launching the Dashboard:
- **One-Click**: Double-click **`run_dashboard.bat`** (or `.\run_dashboard.ps1`).
- **CLI**: `python -m streamlit run dashboard/app.py`
- Open your browser at: **`http://localhost:8501`**

### Summary of the 5 Core Analytical Views:

| View | Name | Visualizations & Business Indicators |
|---|---|---|
| **View 1** | **Overall Performance** | Total Unique Students, Composite Average Grade (0–20), Pass Rate (%), Average Absences, Attendance Rate (%), Final Grade Distribution Histogram with passing line, Student Performance Tier Donut Chart. |
| **View 2** | **Attendance vs Marks** | Absences vs Composite Grade Scatter Plot with OLS linear regression line, Absence Quartile Summary Table, Grade Variance Boxplots across Absence Tiers (`0 (Perfect)`, `1-4 (Low)`, `5-10 (Moderate)`, `>10 (Chronic)`). |
| **View 3** | **Subject Performance** | Mathematics vs Portuguese Course Comparison Table, Semester Trajectory Line Chart ($G1 \rightarrow G2 \rightarrow G3$), Pass vs Fail Grouped Bar Chart by Subject. |
| **View 4** | **Demographic Analysis** | Average Grade by Highest Parental Education Level (`None` $\rightarrow$ `Higher Education`), Study Time Category Boxplots, Gender Performance by Subject, Urban vs Rural Score Breakdown. |
| **View 5** | **Student Profile & Risk Analyzer** | Interactive Student ID Search/Selector, Demographic Dossier Card, Course Marks Breakdown, Grade Evolution Trajectory Line Chart, Risk Status Badge (`High Risk`, `Medium Risk`, `Low Risk`), and Automated Personalized Interventions. |

---

## 12. Validation & Quarantining Results

During execution against the UCI dataset:
- **Total Records Evaluated**: 1,044 records (395 Math, 649 Portuguese).
- **Clean Records Staged**: **1,028 records** routed to `data/staging/staging_students.csv`.
- **Quarantined Records**: **16 records** routed to `data/rejected/rejected_records.csv`.
- **Identified Violation**: Duplicate student registrations within the same subject course.
- **Audit Columns**: Each rejected record includes `rejection_reason` and ISO UTC `rejected_at` timestamp.

---

## 13. Automated Unit Testing

Run the Pytest suite:
```powershell
python -m pytest tests/ -v
```

### Test Coverage (13 / 13 Tests Passed):
- `tests/test_ingestion.py`: Semicolon vs comma delimiter detection, file presence verification, metadata logging.
- `tests/test_validation.py`: Null value handling, grade range bounds ($G1 < 0$, $G3 > 20$), invalid categoricals (`sex='Z'`, `school='XYZ'`), negative absences, duplicate detection within subject.
- `tests/test_transformation.py`: Average calculation, pass/fail threshold, performance category mapping, risk status assignment, relational normalization.

---

## 14. Troubleshooting & FAQ

#### Q: `streamlit: The term 'streamlit' is not recognized`
**A:** Use the Python module launcher:
```powershell
python -m streamlit run dashboard/app.py
```
Or simply double-click `run_dashboard.bat`.

#### Q: `ModuleNotFoundError: No module named 'statsmodels'`
**A:** `dashboard/app.py` computes linear regression directly using built-in NumPy `np.polyfit`. If you want full statsmodels support, install via:
```powershell
pip install statsmodels
```

#### Q: Is Docker required to run this project?
**A:** No. If Docker/PostgreSQL is not running, the pipeline automatically detects it and uses an embedded SQLite database at `data/student_performance.db` with identical schema and functionality.

---

## 15. Submission Checklist (Part 1 — 50 Marks)

- [x] **Dataset**: Official UCI Student Performance dataset (Math & Portuguese) used and documented.
- [x] **Ingestion**: Python/Pandas extraction with metadata logging and pristine raw copy preservation (`src/ingestion/ingest.py`).
- [x] **Raw Layer**: Immutable raw files in `data/raw/`.
- [x] **Validation**: Range bounds (0–20), missing values, domain sets, duplicate student quarantine (`src/validation/validate.py`).
- [x] **Quarantine Log**: `data/rejected/rejected_records.csv` with reason and timestamp.
- [x] **Staging Layer**: Pre-transformation intermediate data in `data/staging/staging_students.csv`.
- [x] **Transformation**: Academic features (`average_grade`, `pass_fail`, `performance_category`, `attendance_rate`, `risk_status`) in `src/transformation/transform.py`.
- [x] **Cleaned Layer**: Relational tables in `data/cleaned/` (`students.csv`, `academic_performance.csv`, `student_analytics.csv`).
- [x] **PostgreSQL Database**: Relational schema DDL (`sql/schema.sql`), analytics mart (`sql/analytics.sql`), and loader with SQLite fallback (`src/database/load.py`).
- [x] **Airflow DAG**: Sequential task graph in `dags/student_pipeline.py`.
- [x] **Streamlit Dashboard**: 5 comprehensive views implemented in `dashboard/app.py`.
- [x] **Unit Testing**: 13 unit tests passing in `tests/`.
- [x] **Launchers**: `run_dashboard.bat`, `run_pipeline.bat` included for one-click grading.
