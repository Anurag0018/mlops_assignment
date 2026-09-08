# ACADEMIC PROJECT REPORT (PART 1)

## Student Performance and Dropout-Risk Prediction System
### Part 1: Unified Academic Data Engineering Pipeline & Decision-Support Mart
**Course:** Data Engineering and MLOps  
**Academic Year:** 2026  
**Assignment:** Project 1 (Part 1 — 50 Marks)  
**Submission Package Item:** Item 8 — Comprehensive Project Report  

---

## Abstract
This project presents an end-to-end, production-grade data engineering pipeline designed to ingest, validate, quarantine, transform, persist, and visualize academic records from secondary educational institutions. Leveraging the University of California, Irvine (UCI) Student Performance Dataset across Mathematics and Portuguese disciplines, the architecture establishes a multi-layered data lakehouse paradigm (`raw`, `staging`, `cleaned`, `rejected`). Data quality is enforced via a declarative validation engine that segregates corrupted or duplicate records into a timestamped audit quarantine log. Cleaned records are normalized into a relational dimensional model (comprising `students` dimension and `academic_performance` fact tables) hosted on PostgreSQL with an embedded SQLite local zero-config fallback. An analytical data mart (`student_analytics`) is synthesized with engineered features, including composite weighted grades, attendance rates, academic performance categories, and early risk flags. The entire workflow is orchestrated via an Apache Airflow DAG (`student_data_pipeline`) with strict task dependency management. An interactive Streamlit dashboard featuring five specialized analytical views provides educational administrators with actionable diagnostic intelligence on student attendance, subject disparity, demographic correlations, and individual student intervention pathways.

---

## Table of Contents
1. [Introduction and Problem Understanding](#1-introduction-and-problem-understanding)
2. [Dataset Identification and Ingestion Architecture](#2-dataset-identification-and-ingestion-architecture)
3. [Data Validation, Quality Framework, and Quarantine Mechanics](#3-data-validation-quality-framework-and-quarantine-mechanics)
4. [Transformation and Academic Feature Engineering](#4-transformation-and-academic-feature-engineering)
5. [Relational Storage and Data Mart Architecture](#5-relational-storage-and-data-mart-architecture)
6. [Pipeline Orchestration with Apache Airflow](#6-pipeline-orchestration-with-apache-airflow)
7. [Visual Analytics and Streamlit Decision-Support Dashboard](#7-visual-analytics-and-streamlit-decision-support-dashboard)
8. [Experimental Verification, Results, and Quality Audit](#8-experimental-verification-results-and-quality-audit)
9. [Conclusion and Transition to Part 2](#9-conclusion-and-transition-to-part-2)

---

## 1. Introduction and Problem Understanding

### 1.1 Background
Secondary education institutions face significant challenges in identifying students at risk of academic failure or course dropout before final examinations take place. Academic performance is influenced by a multi-dimensional matrix of factors, including classroom attendance, study habits, parental involvement, social activities, and institutional support. However, academic data typically resides in siloed repositories—such as Learning Management Systems (LMS), Enterprise Resource Planning (ERP) databases, and administrative spreadsheets. Without an automated, robust data pipeline, educational leaders are limited to reactive evaluations rather than proactive interventions.

### 1.2 Objectives of Part 1
In accordance with the project specification for Part 1 (50 Marks), the objective of this phase is to construct the foundational data engineering architecture without machine learning inference deployment. The explicit goals include:
1. **Automated Multi-Source Ingestion**: Establishing reproducible scripts to ingest disparate CSV datasets while preserving pristine raw copies and recording comprehensive extraction metadata.
2. **Data Validation & Quarantine**: Implementing strict data quality filters (range bounds, domain constraints, null detection, and cross-subject student identity verification) that quarantine defective records into an audited log.
3. **Reproducible Layered Storage**: Maintaining strict separation across `raw/`, `staging/`, `cleaned/`, and `rejected/` data layers.
4. **Relational Database & Data Mart**: Designing and populating a third-normal-form (3NF) relational PostgreSQL warehouse and generating an analytical data mart.
5. **Workflow Orchestration**: Orchestrating the end-to-end ETL flow using an Apache Airflow DAG with fault tolerance and dependency sequencing.
6. **Decision-Support Visualization**: Developing a multi-view Streamlit dashboard that delivers five distinct analytical views for comparative analysis and student profiling.

---

## 2. Dataset Identification and Ingestion Architecture

### 2.1 Dataset Provenance
The pipeline utilizes the **UCI Student Performance Dataset** (Cortez and Silva, 2008), collected from two Portuguese secondary schools (*Escola Secundária Gabriel Pereira* and *Escola Secundária Mousinho da Silveira*):
- **Mathematics Cohort (`student-mat.csv`)**: 395 student enrollments across 33 raw attributes.
- **Portuguese Language Cohort (`student-por.csv`)**: 649 student enrollments across 33 raw attributes.
- **Cross-Subject Population**: 382 students are enrolled concurrently in both courses.

### 2.2 Ingestion Engine (`src/ingestion/ingest.py`)
The ingestion module enforces non-destructive data handling:
- **Delimiter Auto-Detection**: Inspects header delimiters dynamically to seamlessly handle semicolon (`;`) or comma (`,`) delimited CSV files.
- **Remote Bootstrap Capability**: Automatically retrieves authenticated raw files from validated public repositories if not already cached locally.
- **Audit Metadata Logging**: Writes an extraction audit ledger to `data/raw/ingestion_audit.json` capturing ISO 8601 extraction timestamps, absolute source paths, detected row/column dimensions, column headers, and integrity status.
- **Pristine Raw Preservation**: Raw files are written to `data/raw/` in read-only mode and are never manipulated directly by downstream scripts.

---

## 3. Data Validation, Quality Framework, and Quarantine Mechanics

### 3.1 Validation Engine Architecture (`src/validation/validate.py`)
To prevent corrupt or duplicate records from contaminating downstream analytics, every ingested record passes through a validation firewall:

```
[RAW INGESTION]
       │
       ▼
[VALIDATION FIREWALL]
 ├── Check 1: Missing / NULL Values across all attributes
 ├── Check 2: Grade Bounds (0 <= G1, G2, G3 <= 20)
 ├── Check 3: Age Bounds (15 <= age <= 25)
 ├── Check 4: Non-negative Absences (absences >= 0)
 ├── Check 5: Categorical Domains (sex in {M, F}, school in {GP, MS})
 └── Check 6: Intra-subject Student Identity Duplication
       │
   ┌───┴──────────────────────────────┐
   │                                  │
[PASSED RULES]                  [FAILED RULES]
   │                                  │
   ▼                                  ▼
data/staging/staging_students.csv  data/rejected/rejected_records.csv
```

### 3.2 Quarantine Results & Duplicate Discovery
During execution on the raw UCI dataset:
- Total records evaluated: **1,044 records**.
- Successfully validated records routed to `data/staging/`: **1,028 records**.
- Quarantined records routed to `data/rejected/rejected_records.csv`: **16 records**.
- **Root Cause Analysis**: The validation engine discovered 16 duplicate student records within identical subject enrollments (4 in Mathematics, 12 in Portuguese). Each quarantined entry was stamped with its unique demographic student identifier, the specific rejection reason (`Duplicate student record for subject...`), and the UTC timestamp.

---

## 4. Transformation and Academic Feature Engineering

### 4.1 Feature Engineering Logic (`src/transformation/transform.py`)
Operating exclusively on validated staging records, the transformation layer computes key academic indicators:

1. **Composite Average Grade (`average_grade`)**:
   $$\text{Average Grade} = \frac{G_1 + G_2 + G_3}{3}$$
   Rounded to two decimal places, providing a balanced longitudinal measure across all three assessment trimesters.

2. **Pass/Fail Indicator (`pass_fail`)**:
   $$\text{pass\_fail} = \begin{cases} \text{Pass}, & \text{if } G_3 \ge 10 \\ \text{Fail}, & \text{if } G_3 < 10 \end{cases}$$
   Adheres to the official Portuguese secondary grading threshold where 10/20 represents minimum competency.

3. **Performance Classification Tier (`performance_category`)**:
   - `Distinction`: $G_3 \ge 16$ (Outstanding academic excellence)
   - `Good`: $14 \le G_3 < 16$ (Above-average proficiency)
   - `Satisfactory`: $10 \le G_3 < 14$ (Basic competence)
   - `At-Risk`: $G_3 < 10$ (Academic failure requiring immediate remediation)

4. **Normalized Attendance Rate (`attendance_rate`)**:
   $$\text{Attendance Rate (\%)} = \max\left(0, 1 - \frac{\text{absences}}{93}\right) \times 100$$
   Derived from the maximum observable term absence ceiling of 93 sessions.

5. **Parental Education Aggregation (`parent_education`)**:
   Computed as $\max(\text{Medu}, \text{Fedu})$ and mapped to standardized qualitative tiers: *None*, *Primary (4th grade)*, *5th to 9th grade*, *Secondary Education*, or *Higher Education*.

6. **Academic Trajectory (`grade_improvement`)**:
   $$\Delta G = G_3 - G_1$$
   Captures whether a student is on an upward progression or deteriorating trajectory.

7. **Proactive Risk Status (`risk_status`)**:
   - **High Risk**: $G_3 < 10$ AND ($\text{failures} > 0$ OR $\text{absences} > 10$)
   - **Medium Risk**: $G_3 < 10$ OR $\text{failures} > 0$ OR $\text{absences} > 10$
   - **Low Risk**: Passing grades with clean attendance and zero past failures.

---

## 5. Relational Storage and Data Mart Architecture

### 5.1 Relational Schema Design (`sql/schema.sql`)
The relational layer uses a normalized schema:
- **`students` (Dimension Table)**: Captures immutable demographic, home environment, and parental characteristics. Keyed by a deterministic alphanumeric primary key `student_id` (e.g., `STU-69668EB0`). Total unique profiles: **662 students**.
- **`academic_performance` (Fact Table)**: Records course-level facts, weekly study categories, social habits, alcohol consumption indices (`dalc`, `walc`), health scores, absences, attendance percentages, and term marks (`g1`, `g2`, `g3`). Total course facts: **1,028 records**.
- **`ingestion_audit`**: Audit trail recording extraction times and file row counts.

### 5.2 Analytical Data Mart (`sql/analytics.sql`)
The denormalized table `student_analytics` consolidates all dimensions, course facts, and engineered features into a single high-performance query structure.
- **Reporting Views**:
  - `vw_overall_kpis`: Institutional aggregate statistics.
  - `vw_subject_summary`: Math vs Portuguese performance metrics.
  - `vw_attendance_impact`: Performance partitioned across four absence quartiles.
  - `vw_demographic_performance`: Performance by gender, location, and parent education.
  - `vw_at_risk_students`: Active directory of students flagged as High or Medium risk.

### 5.3 Dual-Engine Storage Architecture (`src/database/load.py`)
To prevent setup blockers during grading and evaluation:
- Connects to PostgreSQL (`postgresql://postgres:postgres@localhost:5432/student_db`) when available (native or via `docker compose up -d postgres`).
- If PostgreSQL is offline, a non-blocking socket check smoothly falls back to an embedded SQLite database (`data/student_performance.db`) with equivalent schema and indexing.

---

## 6. Pipeline Orchestration with Apache Airflow

### 6.1 DAG Architecture (`dags/student_pipeline.py`)
The pipeline is formally defined as an Apache Airflow DAG (`student_data_pipeline`) with explicit task dependencies:

```
[start_pipeline] (EmptyOperator)
       │
       ▼
[ingest_raw_data] (PythonOperator -> ingest_all)
       │
       ▼
[validate_and_quarantine] (PythonOperator -> run_validation)
       │
       ▼
[transform_features] (PythonOperator -> run_transformation)
       │
       ▼
[load_postgresql_tables] (PythonOperator -> run_database_load)
       │
       ▼
[build_analytics_mart] (PythonOperator -> query_analytics_data)
       │
       ▼
[pipeline_complete] (EmptyOperator)
```

### 6.2 Execution Reliability
- Configured with `retries: 1`, `retry_delay: 5 minutes`, and daily execution scheduling (`@daily`).
- Includes a standalone CLI mode (`python dags/student_pipeline.py`) enabling complete execution of the DAG task sequence without requiring an active Airflow scheduler daemon.

---

## 7. Visual Analytics and Streamlit Decision-Support Dashboard

The presentation layer is implemented as an interactive Streamlit application (`dashboard/app.py`) featuring five dedicated analytical views:

### View 1: Overall Performance
- **Institutional Metric Cards**: Total Unique Students (662), Average Grade (11.29 / 20), Overall Pass Rate (78.4%), Average Absences (4.6 days), Average Attendance Rate (95.0%).
- **Grade Distribution Histogram**: 21-bin frequency distribution of final marks ($G_3$) color-coded by Pass/Fail with an explicit dashed marker at the 10-point threshold.
- **Performance Category Donut Chart**: Breakdown across Distinction, Good, Satisfactory, and At-Risk tiers.

### View 2: Attendance vs Marks
- **Correlation Scatter Plot**: Absences vs Composite Average Grade with a native NumPy-computed OLS linear regression line showing the negative correlation between chronic absenteeism and academic outcomes.
- **Absence Tier Analysis**: Aggregation table dividing absences into `0 (Perfect)`, `1-4 (Low)`, `5-10 (Moderate)`, and `>10 (Chronic)`.
- **Variance Boxplots**: Illustrates grade dispersion and median deterioration as absence frequency increases.

### View 3: Subject Performance
- **Course Comparative Metrics**: Side-by-side table of Mathematics vs Portuguese enrollment counts, average marks, and pass percentages.
- **Trimester Trajectory Analysis**: Progression line plot tracking mean grades across $G_1 \rightarrow G_2 \rightarrow G_3$ by subject.
- **Pass/Fail Ratios**: Grouped bar visualization showing that Portuguese students achieve higher baseline pass rates (84.5%) compared to Mathematics students (68.3%).

### View 4: Demographic Analysis
- **Parental Education Correlation**: Bar chart proving higher educational attainment of parents correlates with higher student grades.
- **Weekly Study Time Impact**: Box plot comparing academic outcomes across study buckets ($<2$ hrs, 2–5 hrs, 5–10 hrs, $>10$ hrs).
- **Gender & Residence Breakdown**: Cross-tabulated performance metrics comparing male vs female performance and urban vs rural student achievements.

### View 5: Student Profile & Risk Analyzer
- **Interactive Student Selector**: Dropdown search by `student_id`.
- **Dossier Card**: Displays student demographics, school, age, living area, parental education, and risk badge.
- **Course Breakdown Table**: Displays exact $G_1, G_2, G_3$ scores and trajectories across all enrolled subjects.
- **Individual Trimester Progression Chart**: Line graph visualizing student score evolution.
- **Personalized Recommendation Engine**: Generates targeted pedagogical intervention advice (e.g., Mandatory Tutoring, Study Skills Workshop, or Enrichment Programs).

---

## 8. Experimental Verification, Results, and Quality Audit

### 8.1 Automated Unit Test Verification
An automated test suite (`tests/`) containing 13 unit tests was executed via `pytest`:
- `tests/test_ingestion.py`: Verified delimiter detection, missing file exception handling, and audit logging.
- `tests/test_validation.py`: Verified rejection of out-of-range marks ($G_1 = -5, G_3 = 25$), invalid gender values, negative absences, nulls, and duplicate student records.
- `tests/test_transformation.py`: Verified composite grade calculations, pass/fail thresholding, performance classification, and risk flagging.
- **Test Result**: **13 Passed in 1.79s (100% Pass Rate)**.

### 8.2 End-to-End Pipeline Metrics
| Metric | Value |
|---|---|
| Total Raw Rows Evaluated | 1,044 |
| Clean Rows Staged | 1,028 |
| Quarantined Invalid/Duplicate Rows | 16 |
| Unique Normalized Students | 662 |
| Total Academic Performance Records | 1,028 |
| Total Data Mart Records | 1,028 |
| Overall Mean Grade | 11.29 / 20.00 |
| Overall Institutional Pass Rate | 78.40% |
| High Risk Identified Students | 116 |

---

## 9. Conclusion and Transition to Part 2

### 9.1 Summary of Part 1 Deliverables
Part 1 of the Student Performance and Dropout-Risk Prediction System successfully delivers a unified data pipeline that satisfies all requirements outlined in the 50-mark project specification:
1. Automated ingestion preserving raw source integrity.
2. An audited validation engine with duplicate student quarantine logging.
3. Feature engineering generating robust academic indicators.
4. Relational 3NF PostgreSQL storage and an analytical data mart.
5. Airflow DAG orchestration with standalone execution support.
6. A 5-view Streamlit interactive dashboard providing decision-support intelligence.

### 9.2 Interface to Part 2 (MLOps Pipeline Extension)
In accordance with course guidelines, Part 1 maintains strict boundaries by omitting machine learning deployment. However, the data mart (`student_analytics`) created in this phase is engineered to serve as the ground truth training set for Part 2:
- **Prediction Targets Ready**: `risk_status`, `pass_fail`, and `final_grade` are pre-computed.
- **Feature Store Ready**: Clean numerical, ordinal, and encoded categorical attributes are accessible via SQL or CSV for train/test splitting.
- **Next Steps for Part 2**: Model training (Random Forest, XGBoost), experiment tracking via MLflow, data versioning via DVC, inference serving via FastAPI, and continuous drift monitoring.
