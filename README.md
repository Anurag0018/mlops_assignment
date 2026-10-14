# Student Performance & Academic Dropout-Risk Prediction System (Data Engineering & MLOps Platform)

## Project Overview

This project implements an enterprise-grade, end-to-end **Data Engineering and MLOps Platform** for predicting student academic performance and academic failure risk (`final_grade < 10`):

- **Part 1 — Data Engineering Foundation:** Automated ingestion, multi-stage schema validation, quarantine logging, relational PostgreSQL modeling, analytical data mart creation, Airflow ETL orchestration, and executive Streamlit analytical dashboards.
- **Part 2 — Production MLOps Lifecycle:** Leak-free feature pipelines, multi-model benchmarking (Logistic Regression, Random Forest, XGBoost), MLflow experiment tracking, model registry governance, FastAPI prediction microservice, Docker containerization, Population Stability Index (PSI) drift monitoring, and champion-vs-challenger automated retraining loops.

### 🌐 Live Cloud Deployment & Quick Links

- **🚀 Live Interactive Streamlit App:** [https://mlopsassignment-sm7scsm4tgafclq2hegef9.streamlit.app/](https://mlopsassignment-sm7scsm4tgafclq2hegef9.streamlit.app/)
- **📦 GitHub Repository:** [https://github.com/Riyan-ai-code/mlops_assignment_an](https://github.com/Riyan-ai-code/mlops_assignment_an)
- **⚡ Local API Microservice:** `http://localhost:8000` (Swagger UI: `http://localhost:8000/docs`)
- **📊 Local MLflow Tracking UI:** `http://localhost:5000`

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
- Apache Airflow 3.3.1
- PythonOperator / EmptyOperator
- Airflow DAG task dependencies
- Graphviz for DAG visualization

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

Apache Airflow 3.3.1 is used to orchestrate the complete Part 1 data pipeline.

The DAG is defined in:

```text
dags/student_pipeline.py
```

### DAG Task Sequence

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

### Airflow DAG Visualization

The following graph is generated directly from the Airflow DAG using the Airflow CLI and Graphviz.

![Airflow DAG Workflow](docs/airflow_dag.png)

### Airflow Setup

For local development on Windows, use Ubuntu/WSL2 rather than native Windows Airflow.

Create and activate the virtual environment:

```bash
python3 -m venv airflow-venv
source airflow-venv/bin/activate
```

Install Airflow:

```bash
pip install apache-airflow
```

Install Graphviz for DAG visualization:

```bash
sudo apt update
sudo apt install graphviz
pip install graphviz
```

Configure Airflow to use the repository DAG folder:

```bash
export AIRFLOW__CORE__DAGS_FOLDER=/home/anurag/project/mlops_assignment/dags
```

Verify that the DAG is registered:

```bash
airflow dags list | grep student_data_pipeline
```

Generate the DAG visualization:

```bash
airflow dags show student_data_pipeline --save docs/airflow_dag.png
```

### Start Airflow

For a simple local setup:

```bash
airflow standalone
```

The Airflow UI can then be opened at:

```text
http://localhost:8080
```

To trigger the DAG from the CLI:

```bash
airflow dags trigger student_data_pipeline
```

### Local Pipeline Testing

The pipeline functions can also be tested directly without the Airflow scheduler when required by the coursework. The Airflow DAG itself should be validated through Airflow.

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

For Airflow 3.3.1 local development, create a separate Airflow virtual environment if Airflow is not included in the project's requirements:

```bash
python3 -m venv airflow-venv
source airflow-venv/bin/activate
pip install apache-airflow
sudo apt update
sudo apt install graphviz
pip install graphviz
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

### Airflow

Set the repository DAG directory before using Airflow:

```bash
export AIRFLOW__CORE__DAGS_FOLDER=/home/anurag/project/mlops_assignment/dags
```

List the DAG:

```bash
airflow dags list | grep student_data_pipeline
```

Start the local Airflow environment:

```bash
airflow standalone
```

Trigger the pipeline:

```bash
airflow dags trigger student_data_pipeline
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
- [x] Airflow DAG visualization evidence (`docs/airflow_dag.png`)
- [x] Streamlit dashboard with 5 views
- [x] Architecture diagram
- [x] Data dictionary
- [x] Validation rules
- [x] Unit tests
- [x] End-to-end execution evidence
- [x] README setup instructions

---

## 19. Execution Evidence

The repository includes an Airflow-generated DAG visualization at:

```text
docs/airflow_dag.png
```

This image is generated from the registered `student_data_pipeline` DAG using:

```bash
airflow dags show student_data_pipeline --save docs/airflow_dag.png
```

Additional execution evidence can include Airflow UI screenshots, task logs, PostgreSQL table output, validation/rejection records, and the Streamlit dashboard.

---

## 20. Part 2 — End-to-End MLOps System Implementation

Part 2 extends the Part 1 data engineering foundation into a fully reproducible, production-grade MLOps system for student academic failure risk prediction (`final_grade < 10`).

```text
[ Data Mart: student_analytics.csv (1,028 rows) ]
                       ↓
   [ Feature Engineering & Leakage Isolation ]
   - 16 Predictors (6 Numerical, 10 Categorical)
   - ColumnTransformer (StandardScaler + OneHotEncoder)
   - Stratified Split (70% Train, 15% Val, 15% Test)
                       ↓
         [ MLflow Experiment Tracking ]
   - Logistic Regression (Baseline, balanced)
   - Random Forest Classifier (150 trees, balanced)
   - XGBoost Classifier (Champion, scale_pos_weight=3.64)
   - Evaluated on Accuracy, Precision, Recall, F1, ROC-AUC
                       ↓
        [ Model Governance & Versioning ]
   - Champion Model: models/best_model.joblib
   - Lineage & Registry: models/model_registry.json (v1.0.0)
   - Evaluation Plots: reports/ (CM, ROC, PR Curves)
                       ↓
       [ FastAPI Microservice (Port 8000) ]
   - GET /health, GET /model-info, GET /metrics
   - POST /predict (Single), POST /predict/batch (Roster)
   - Pydantic validation, latency tracking, Docker containerized
                       ↓
   [ Streamlit Portal: Views 6 & 7 Integrated ]
   - View 6: Real-Time Risk Prediction & Cohort Scoring
   - View 7: MLOps Model Governance & Drift Diagnostics
                       ↓
       [ Monitoring & Continuous Retraining ]
   - Population Stability Index (PSI) Feature Drift Detection
   - Champion-vs-Challenger Promotion Criteria (F1 + Recall floor)
```

---

### 20.1 Prediction Target Formulation & Zero Leakage

- **Target Variable:** `failure_risk` $\in \{0, 1\}$
  - $1 = \text{Academic Failure Risk} \ (G3 < 10)$
  - $0 = \text{Passing Trajectory} \ (G3 \ge 10)$
- **Defensibility:** In Portuguese secondary education, 10 on a 20-point scale is the universal legal passing threshold. Identifying students likely to score below 10 allows early academic intervention before final evaluations.
- **Class Distribution:**
  - Total Validated Records: 1,028
  - Passing (`0`): 806 records (78.4%)
  - At-Risk (`1`): 222 records (21.6%)
  - Class imbalance ratio: $\approx 3.64:1$ (handled via balanced weights and positive class scaling).
- **Zero Target Leakage Guarantee:**
  - **Excluded Predictors:** $G2$ (Second Period Grade), $G3$ (Final Grade), `final_grade`, `average_grade`, `pass_fail`, `performance_category`, `grade_improvement`, `risk_status`, and `student_id`.
  - **Included Predictors:** Only baseline attributes available early in the academic period:
    - Numerical (6): `g1` (Period 1 checkpoint), `age`, `absences`, `attendance_rate`, `studytime`, `failures`.
    - Categorical (10): `school`, `sex`, `address`, `famsize`, `pstatus`, `mjob`, `fjob`, `parent_education`, `study_time_category`, `subject`.

---

### 20.2 Feature Engineering Pipeline

Implemented in `src/features/build_features.py`:
- **Transformers:** Scikit-Learn `ColumnTransformer` applying `StandardScaler` to numerical predictors and `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` to categorical predictors.
- **Transformed Dimensions:** 37 transformed feature dimensions (6 scaled numerical + 31 one-hot categories).
- **Leak-Free Protocol:** Preprocessor is fitted strictly on the Training split (719 records) and used to transform Validation (154 records) and Test (155 records) splits without data leakage.
- **Exported Lineage Artifacts:**
  - `models/preprocessor.joblib`: Serialized fitted ColumnTransformer.
  - `models/feature_metadata.json`: Feature schemas, allowed categories, and numerical bounds.
  - `data/reference/reference_features.parquet`: Training baseline features for PSI drift detection.
  - `data/reference/dataset_fingerprint.json`: Dataset SHA-256 fingerprint, row counts, and class balance.

---

### 20.3 Model Benchmarking & Empirical Results

Implemented in `src/training/train.py` with multi-model benchmarking:

| Model Candidate | Val Accuracy | Val Precision | Val Recall | Val F1-Score | Val ROC-AUC | Test F1-Score | Test Recall | Test ROC-AUC |
|---|---|---|---|---|---|---|---|---|
| **Logistic Regression (Baseline)** | 86.36% | 0.6579 | 0.7576 | 0.7042 | 0.9256 | 0.6914 | 0.8235 | 0.9409 |
| **Random Forest Classifier** | 87.66% | 0.7188 | 0.6970 | 0.7077 | 0.9276 | 0.6944 | 0.7353 | 0.9186 |
| **XGBoost Classifier (Champion)** | **88.96%** | **0.7000** | **0.8485** | **0.7671** | **0.9329** | **0.7013** | **0.7941** | **0.9220** |

#### Champion Model Selection Rationale
In an educational early-warning system, **Recall is paramount** — failing to identify an at-risk student (False Negative) has severe educational consequences, while producing an alert for a student who passes (False Positive) merely leads to additional advisory support.
- **XGBoost Classifier** was selected as the **Champion Model** because it achieved the highest Validation Recall (**84.85%**) while maintaining the highest Validation F1-Score (**0.7671**) and ROC-AUC (**0.9329**), generalising cleanly to the unseen Test split (Test F1: 0.7013, Test Recall: 79.41%, Test ROC-AUC: 0.9220).

---

### 20.4 MLflow Experiment Tracking & Governance

Implemented in `src/tracking/mlflow_utils.py`:
- **Tracking Backend:** Local SQLite database at `sqlite:///mlruns.db`.
- **Experiment Name:** `student_performance_mlops`.
- **Tracked Parameters & Metrics:** Hyperparameters, train/val/test metrics, class weights, random seeds, and pipeline tags.
- **Saved Evaluation Artifacts:**
  - `reports/cm_xgboost_classifier.png`: Confusion Matrix on Test Split.
  - `reports/roc_xgboost_classifier.png`: ROC Curve (AUC = 0.922).
  - `reports/pr_xgboost_classifier.png`: Precision-Recall Curve (AP = 0.753).
- **Model Registry Governance:** `models/model_registry.json` tracks model version (`v1.0.0`), champion algorithm, hyperparameter specs, and candidate comparisons.

To launch the MLflow UI:
```bash
run_mlflow_ui.bat
# Or manually:
mlflow ui --backend-store-uri sqlite:///mlruns.db --port 5000
```
Open [http://localhost:5000](http://localhost:5000) to inspect all logged runs and parameters.

---

### 20.5 FastAPI Prediction Microservice

Implemented in `api/`:
- `api/main.py`: REST application with CORS middleware, structured logging, and lifespan management.
- `api/schemas.py`: Pydantic validation schemas with boundary validation.
- `api/services.py`: High-performance singleton model service with latency tracking.

#### Available Endpoints
- `GET /health` — Service readiness and model status.
- `GET /model-info` — Model version, algorithm, metrics, and feature schema.
- `POST /predict` — Single student academic failure risk prediction.
- `POST /predict/batch` — Vectorized batch prediction for multi-student cohorts.
- `GET /metrics` — Operational metrics: total requests, at-risk alerts, average latency (ms).

To launch the FastAPI microservice:
```bash
run_api.bat
# Or manually:
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

#### Example Inference Request
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "g1": 6.0,
    "age": 18,
    "absences": 18,
    "attendance_rate": 80.6,
    "studytime": 1,
    "failures": 2,
    "school": "MS",
    "sex": "M",
    "address": "R",
    "famsize": "LE3",
    "pstatus": "A",
    "mjob": "at_home",
    "fjob": "other",
    "parent_education": "Primary (4th grade)",
    "study_time_category": "<2 hours",
    "subject": "Mathematics"
  }'
```

---

### 20.6 Docker Containerization

- `api/Dockerfile`: Multi-stage Python 3.12-slim container with built-in healthchecks.
- `docker-compose.yml`: Multi-container stack orchestrating:
  1. `postgres` (port 5432) — Relational warehouse and data mart.
  2. `api` (port 8000) — FastAPI prediction microservice.
  3. `dashboard` (port 8501) — Streamlit executive portal.

To build and run the entire stack:
```bash
docker-compose up --build
```

---

### 20.7 Streamlit Dashboard Extensions (Views 6 & 7)

The Streamlit portal (`dashboard/app.py`) provides 7 comprehensive tabs:
- **View 1:** Executive KPI Summary & Grade Distributions.
- **View 2:** Attendance Impact, Scatter Correlation & Chronic Absenteeism.
- **View 3:** Subject Performance Comparison (Mathematics vs Portuguese).
- **View 4:** Socio-Demographic & Parental Education Success Indicators.
- **View 5:** Student Diagnostic Dossier & Academic Early Warning System.
- **View 6: 🎯 Real-Time Academic Risk Prediction (ML Inference):**
  - Interactive student profile configuration (Period 1 grades, absences, study habits).
  - Risk gauge indicator displaying failure probability % and Risk Level (Low, Medium, High).
  - Actionable pedagogical intervention guidance.
  - Vectorized batch cohort scoring across the active filtered data mart.
- **View 7: 📈 MLOps Model Governance & Drift Diagnostics:**
  - Active champion model specifications and version lineage (`v1.0.0`).
  - Empirical model candidate comparison leaderboard.
  - Evaluation artifact visualizer (Confusion Matrix, ROC Curve, PR Curve).
  - Population Stability Index (PSI) feature drift table with health status indicators.
  - Documented model retraining policy and promotion rules.

To run the dashboard locally:
```bash
run_dashboard.bat
# Or manually:
streamlit run dashboard/app.py
```

**🌐 Live Cloud Hosted App:**
The portal is publicly accessible on Streamlit Community Cloud at:
[https://mlopsassignment-sm7scsm4tgafclq2hegef9.streamlit.app/](https://mlopsassignment-sm7scsm4tgafclq2hegef9.streamlit.app/)


---

### 20.8 Monitoring & Retraining Pipeline

- **Data Quality Validation (`src/monitoring/data_quality.py`):**
  - Validates inference records against feature ranges and allowed categorical sets.
  - Calculates batch health score % and flags out-of-range features.
- **Feature Drift Detection (`src/monitoring/drift.py`):**
  - Computes Population Stability Index (PSI) against `data/reference/reference_features.parquet`.
  - **Thresholds:**
    - $\text{PSI} < 0.10$: Stable distribution (No Drift).
    - $0.10 \le \text{PSI} < 0.20$: Moderate distribution shift (Warning / Monitor).
    - $\text{PSI} \ge 0.20$: Critical distribution drift (Triggers Retraining Alert).
- **Automated Retraining Loop (`src/training/retrain.py`):**
  - Trains challenger models on updated analytical data.
  - **Promotion Criteria:**
    - Challenger must improve Validation F1-Score over Champion by $\Delta \ge 0.005$.
    - Validation Recall must remain $\ge 0.70$ (Recall safety floor).
  - Upon promotion, model version increments (e.g., `v1.1.0`), artifacts update, and promotion lineage is committed to `models/model_registry.json`.

---

### 20.9 Automated Testing Suite

The repository includes **37 automated unit and integration tests** covering the entire Data Engineering and MLOps lifecycle:

```bash
python -m pytest tests/ -v
```

Test coverage includes:
- `tests/test_ingestion.py` (3 tests): Ingestion delimiters, missing file handling, raw data integrity.
- `tests/test_validation.py` (7 tests): Data schema boundaries, quarantine logic, duplicate isolation.
- `tests/test_transformation.py` (3 tests): Academic metric engineering and dimensional normalization.
- `tests/test_features.py` (4 tests): Zero target leakage audit, dataset fingerprinting, ColumnTransformer dimensions, stratified splits.
- `tests/test_training.py` (4 tests): Metric computation math, artifact serialization, model inference, registry schemas.
- `tests/test_api.py` (7 tests): `/health`, `/model-info`, `/predict`, `/predict/batch`, `/metrics`, and validation errors.
- `tests/test_monitoring.py` (6 tests): Data quality validation, numerical and categorical PSI drift calculations, end-to-end drift reporting.
- `tests/test_retrain.py` (3 tests): Champion-vs-challenger promotion criteria and recall safety floor enforcement.

---

### 20.10 Part 2 Submission Checklist

- [x] Defensible academic risk target formulated (`failure_risk`, $G3 < 10$).
- [x] Leak-free feature engineering pipeline with `ColumnTransformer`.
- [x] Multi-model training & benchmarking (Logistic Regression, Random Forest, XGBoost).
- [x] MLflow experiment tracking (`sqlite:///mlruns.db`).
- [x] Registered Champion Model (`models/best_model.joblib` and `models/model_registry.json`).
- [x] Evaluation artifacts generated (Confusion Matrix, ROC Curve, PR Curve).
- [x] Versioning metadata via `params.yaml`, `dvc.yaml`, and dataset fingerprints.
- [x] Production FastAPI prediction microservice with Pydantic validation.
- [x] Dockerfile containerization (`api/Dockerfile` and `docker-compose.yml`).
- [x] Streamlit dashboard extended with View 6 (Risk Prediction) and View 7 (MLOps Governance & Drift).
- [x] PSI feature drift engine and data quality validator.
- [x] Documented model retraining loop with champion-vs-challenger promotion criteria.
- [x] Comprehensive automated test suite (37 tests passing).
- [x] GitHub Actions CI workflow (`.github/workflows/ci.yml`).
- [x] Live interactive deployment on Streamlit Community Cloud ([https://mlopsassignment-sm7scsm4tgafclq2hegef9.streamlit.app/](https://mlopsassignment-sm7scsm4tgafclq2hegef9.streamlit.app/)).

---

### 20.11 Live Cloud Deployment & Cross-Platform Resilience

#### 1. Streamlit Community Cloud Architecture
- **Hosted Portal URL:** [https://mlopsassignment-sm7scsm4tgafclq2hegef9.streamlit.app/](https://mlopsassignment-sm7scsm4tgafclq2hegef9.streamlit.app/)
- **Repository Source:** `https://github.com/Riyan-ai-code/mlops_assignment_an` (Branch: `master`, Entrypoint: `dashboard/app.py`)
- **Runtime Environment:** Managed Python container automatically provisioned using `requirements.txt`.
- **Integrated Model Artifacts:** Uses the serialized Champion XGBoost model (`models/best_model.joblib`), fitted `ColumnTransformer` (`models/preprocessor.joblib`), and baseline feature reference distributions (`data/reference/reference_features.parquet`) for real-time drift computation without requiring an external database cluster.
- **SQLite Analytics Mart:** Automatically bootstraps using the local relational SQLite data mart (`student_performance.db` / `data/cleaned/student_analytics.csv`) ensuring zero cold-start failures.

#### 2. Cross-Platform Environment Portability Fixes
- **MLflow Tracking Portability:**
  - Enhanced `src/tracking/mlflow_utils.py` with dynamic experiment artifact location resolution.
  - Automatically heals any legacy absolute path bindings (such as machine-specific drives or paths) on clone, redirecting artifact repositories smoothly to `mlruns/<experiment_id>` in the active repository root.
- **Python Runtime Compatibility:**
  - Fully verified across Python 3.10, 3.11, and 3.12 environments.
  - All 37 automated tests pass natively on both Windows and Linux CI environments.


---

## 21. License / Academic Use

This repository is an individual academic project for the Data Engineering and MLOps coursework. Public datasets are used according to their respective terms.

