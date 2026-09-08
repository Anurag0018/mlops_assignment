# Student Performance Data Engineering Pipeline — Part 1

## Project Overview

This project implements **Part 1 of the Data Engineering and MLOps coursework** for the Student Performance and Dropout-Risk Prediction System.

The objective of Part 1 is to build a reliable, reproducible data engineering pipeline that:

- acquires and documents student performance data
- ingests raw CSV data using Python and Pandas
- preserves the raw data layer
- validates and quarantines invalid records
- creates staging, cleaned, and analytical data layers
- transforms academic records into useful analytical indicators
- stores the processed data in PostgreSQL
- creates an analytical data mart
- orchestrates the pipeline using Apache Airflow
- provides an interactive Streamlit dashboard

**Part 1 does not include machine-learning model training, MLflow, FastAPI, model deployment, or model monitoring. Those belong to Part 2.**

---

## 1. Problem Statement

Educational institutions collect academic information from different sources such as assessment records, assignment records, attendance data, and learning-management systems. Raw data may contain missing values, duplicate records, invalid values, and inconsistent formats.

This project creates a reproducible data pipeline that converts student performance data into reliable analytical datasets that can be used for academic reporting and decision support.

The final Part 1 flow is:

```text
Dataset
   ↓
Python / Pandas Ingestion
   ↓
Raw Layer
   ↓
Data Validation
   ├── Invalid Records → Rejected / Error Log
   ↓
Staging Layer
   ↓
Transformation
   ↓
Cleaned Data
   ↓
PostgreSQL
   ↓
Analytical Data Mart
   ↓
Streamlit Dashboard
```

Apache Airflow is used to orchestrate the pipeline stages.

---

## 2. Part 1 Requirements

| Requirement | Implementation |
|---|---|
| Dataset acquisition and documentation | UCI Student Performance Dataset |
| Reproducible ingestion | Python + Pandas |
| Raw data preservation | `data/raw/` |
| Data validation | Python validation module |
| Rejected-record log | `data/rejected/` |
| Staging layer | `data/staging/` |
| Transformation | Python + Pandas |
| Cleaned layer | `data/cleaned/` |
| Database | PostgreSQL |
| Analytical table / data mart | `student_analytics` |
| Orchestration | Apache Airflow |
| Dashboard | Streamlit |
| Data dictionary | `docs/data_dictionary.md` |
| Validation rules | `docs/validation_rules.md` |
| Architecture diagram | `docs/architecture.svg` |
| Automated tests | Pytest |
| Execution evidence | Screenshots / logs |
| Setup documentation | `README.md` |

---

## 3. Dataset

The project uses the **UCI Student Performance Dataset**.

### Sources

- `student-mat.csv` — Mathematics course
- `student-por.csv` — Portuguese language course

The dataset contains demographic, family, study-habit, attendance, and academic performance attributes.

Important attributes include:

- School
- Sex
- Age
- Address
- Family size
- Parent education
- Parent occupation
- Study time
- Previous failures
- Absences
- G1 — first-period grade
- G2 — second-period grade
- G3 — final grade

The grade fields use a **0–20 scale**.

Source:

https://archive.ics.uci.edu/dataset/320/student+performance

---

## 4. Technology Stack

### Programming
- Python 3.10+
- Pandas
- NumPy

### Data Engineering
- Python ETL scripts
- Data validation
- Feature engineering
- CSV-based raw/staging/cleaned layers

### Database
- PostgreSQL
- SQLAlchemy
- Psycopg2
- SQLite fallback for local development

### Orchestration
- Apache Airflow
- PythonOperator / Airflow task dependencies

### Visualization
- Streamlit
- Plotly

### Testing
- Pytest

### Containerization
- Docker
- Docker Compose

---

## 5. Pipeline Architecture

```text
┌──────────────────────────────┐
│        UCI Dataset           │
│ student-mat.csv              │
│ student-por.csv              │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│       Data Ingestion         │
│ Python + Pandas              │
│ Source / date / row-count    │
│ audit metadata               │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│          Raw Layer           │
│       data/raw/              │
│ Pristine source copies       │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│       Validation Layer       │
│ Missing values               │
│ Duplicate records            │
│ Grade range 0–20             │
│ Valid categorical values     │
└──────────────┬───────────────┘
               │
        ┌──────┴──────┐
        ↓             ↓
   Valid records   Invalid records
        ↓             ↓
   Staging layer   Rejected log
        │
        ↓
┌──────────────────────────────┐
│       Transformation         │
│ Academic metrics             │
│ Aggregations                 │
│ Performance indicators       │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│        Cleaned Layer         │
│ students.csv                 │
│ academic_performance.csv     │
│ student_analytics.csv        │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│         PostgreSQL           │
│ students                     │
│ academic_performance         │
│ student_analytics            │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│      Streamlit Dashboard     │
│ KPIs / Attendance / Subjects │
│ Demographics / Student View  │
└──────────────────────────────┘

Apache Airflow orchestrates the pipeline stages.
```

---

## 6. Project Structure

```text
mlops_assignment/
│
├── data/
│   ├── raw/
│   │   ├── student-mat.csv
│   │   ├── student-por.csv
│   │   └── ingestion_audit.json
│   │
│   ├── staging/
│   │   └── staging_students.csv
│   │
│   ├── cleaned/
│   │   ├── students.csv
│   │   ├── academic_performance.csv
│   │   └── student_analytics.csv
│   │
│   └── rejected/
│       └── rejected_records.csv
│
├── src/
│   ├── ingestion/
│   │   └── ingest.py
│   ├── validation/
│   │   └── validate.py
│   ├── transformation/
│   │   └── transform.py
│   └── database/
│       └── load.py
│
├── dags/
│   └── student_pipeline.py
│
├── sql/
│   ├── schema.sql
│   └── analytics.sql
│
├── dashboard/
│   └── app.py
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_validation.py
│   └── test_transformation.py
│
├── docs/
│   ├── architecture.svg
│   ├── data_dictionary.md
│   └── validation_rules.md
│
├── requirements.txt
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 7. Data Ingestion

The ingestion module reads the source CSV files using Pandas.

The ingestion process:

1. verifies that the source files exist
2. detects the CSV delimiter
3. reads the data
4. records the extraction date/time
5. records the source file
6. records the row count
7. writes an ingestion audit record
8. preserves a raw copy in `data/raw/`

Example:

```bash
python src/ingestion/ingest.py
```

The raw data is not manually modified after ingestion.

---

## 8. Data Validation

The validation stage checks the incoming records before transformation.

### Main validation rules

#### Grade validation

```text
0 ≤ G1 ≤ 20
0 ≤ G2 ≤ 20
0 ≤ G3 ≤ 20
```

#### Attendance validation

```text
absences ≥ 0
```

#### Categorical validation

Examples:

```text
sex ∈ {F, M}
school ∈ {GP, MS}
address ∈ {U, R}
```

#### Missing values

Required fields are checked for missing values.

#### Duplicate records

Duplicate student-course records are detected and quarantined.

Invalid records are written to:

```text
data/rejected/rejected_records.csv
```

Each rejected record contains a rejection reason and timestamp.

---

## 9. Data Layers

### Raw Layer

```text
data/raw/
```

Contains the original extracted source files.

### Staging Layer

```text
data/staging/
```

Contains records that passed validation and are ready for transformation.

### Cleaned Layer

```text
data/cleaned/
```

Contains normalized datasets prepared for database loading.

### Analytical Layer

```text
student_analytics
```

Contains derived academic indicators optimized for dashboard reporting.

---

## 10. Transformation and Feature Engineering

The transformation stage creates analytical indicators from the validated data.

Examples include:

- `average_grade`
- `pass_fail`
- `performance_category`
- `attendance_rate`
- `grade_improvement`

The transformation also separates the data into relational entities such as:

```text
students
academic_performance
student_analytics
```

All transformations are performed programmatically so that the pipeline remains reproducible.

---

## 11. PostgreSQL Database

The database contains the main relational tables.

### `students`

Stores student demographic and family information.

### `academic_performance`

Stores course-level academic information such as:

- study time
- previous failures
- absences
- G1
- G2
- G3

### `ingestion_audit`

Stores ingestion metadata such as:

- source
- extraction timestamp
- row count
- file status

### `student_analytics`

Analytical data mart containing transformed indicators used by the dashboard.

SQL files:

```text
sql/schema.sql
sql/analytics.sql
```

---

## 12. Apache Airflow

The Airflow DAG orchestrates the complete pipeline.

Task sequence:

```text
start_pipeline
      ↓
ingest_raw_data
      ↓
validate_and_quarantine
      ↓
transform_features
      ↓
load_postgresql_tables
      ↓
build_analytics_mart
      ↓
pipeline_complete
```

DAG file:

```text
dags/student_pipeline.py
```

The pipeline can also be executed directly without Airflow for local testing:

```bash
python dags/student_pipeline.py
```

---

## 13. Streamlit Dashboard

The dashboard provides at least five meaningful analytical views.

### View 1 — Overall Performance

Shows:

- total students
- average grade
- pass rate
- average absences
- attendance rate
- grade distribution
- performance categories

### View 2 — Attendance vs Marks

Shows:

- absences vs grades
- attendance impact
- absence groups
- grade distributions

### View 3 — Subject Performance

Compares:

- Mathematics
- Portuguese

and shows:

- G1 → G2 → G3 progression
- pass/fail distribution
- subject-level performance

### View 4 — Demographic Analysis

Shows academic performance by:

- gender
- location
- parental education
- study time

### View 5 — Student Profile

Allows an individual student record to be explored through:

- demographic information
- course marks
- absences
- grade progression
- performance indicators

**Note:** Any "risk" indicator in Part 1 is a rule-based analytical indicator only. It is not an ML prediction model.

Launch:

```bash
python -m streamlit run dashboard/app.py
```

Dashboard:

```text
http://localhost:8501
```

---

## 14. Testing

Run:

```bash
python -m pytest tests/ -v
```

Tests cover:

- ingestion
- delimiter handling
- metadata generation
- validation rules
- missing values
- invalid grades
- invalid categorical values
- duplicate detection
- feature calculations
- performance categorization

---

## 15. Installation

### 1. Clone the repository

```bash
git clone https://github.com/Anurag0018/mlops_assignment.git
cd mlops_assignment
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy:

```text
.env.example
```

to:

```text
.env
```

Set database credentials through environment variables.

Example:

```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/student_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=student_db
DB_USER=postgres
DB_PASSWORD=postgres
```

Do not commit real passwords or credentials.

---

## 16. Running the Project

### Complete pipeline

```bash
python dags/student_pipeline.py
```

### Individual stages

```bash
python src/ingestion/ingest.py
python src/validation/validate.py
python src/transformation/transform.py
python src/database/load.py
```

### Dashboard

```bash
python -m streamlit run dashboard/app.py
```

### Tests

```bash
python -m pytest tests/ -v
```

---

## 17. Expected End-to-End Demonstration

The final demonstration should show:

```text
1. Source dataset
       ↓
2. Ingestion execution
       ↓
3. Raw data created
       ↓
4. Validation execution
       ↓
5. Valid + rejected records
       ↓
6. Staging data
       ↓
7. Transformation
       ↓
8. Cleaned data
       ↓
9. PostgreSQL tables
       ↓
10. Analytical data mart
       ↓
11. Streamlit dashboard
```

This demonstrates the complete Part 1 pipeline from **data ingestion to dashboard output**.

---

## 18. Part 1 Submission Checklist

- [x] Dataset source documented
- [x] Python/Pandas ingestion
- [x] Raw data layer
- [x] Ingestion metadata
- [x] Data validation
- [x] Rejected-record/error log
- [x] Staging layer
- [x] Transformation and feature engineering
- [x] Cleaned data layer
- [x] PostgreSQL schema
- [x] Analytical data mart
- [x] Apache Airflow DAG
- [x] Streamlit dashboard with 5 views
- [x] Architecture diagram
- [x] Data dictionary
- [x] Validation rules
- [x] Unit tests
- [x] End-to-end execution evidence
- [x] README setup instructions

---

## 19. Part 2 — Future Extension

Part 2 will extend this Part 1 pipeline into an MLOps workflow.

Possible future components include:

- prediction target definition
- Logistic Regression
- Random Forest
- XGBoost
- MLflow
- model registry
- DVC/Git-based versioning
- FastAPI
- Dockerized inference
- data/model monitoring
- drift detection
- retraining

**These components are intentionally excluded from the current Part 1 implementation.**

---

## License / Academic Use

This repository is an individual academic project for the Data Engineering and MLOps coursework. Public datasets are used according to their respective terms.

