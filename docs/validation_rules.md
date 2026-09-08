# Data Validation Framework & Business Rules

This document specifies the validation architecture, rejection policies, and quarantine mechanics implemented in the Student Performance Data Engineering Pipeline (`src/validation/validate.py`).

---

## 1. Overview of Data Quality Lifecycle

```
[RAW LAYER (data/raw/)]
         │
         ▼
[VALIDATION ENGINE (src/validation/validate.py)]
         │
    ┌────┴──────────────────────────────┐
    │                                   │
[PASSED]                            [FAILED]
    │                                   │
    ▼                                   ▼
[STAGING LAYER]                     [REJECTED LAYER]
(data/staging/staging_students.csv) (data/rejected/rejected_records.csv)
```

---

## 2. Validation Rules & Rejection Matrix

| Rule Category | Field(s) | Condition / Threshold | Violation Action | Error Message |
|---|---|---|---|---|
| **Missing Values** | Any column | `IS NULL` or `NaN` | Reject & Quarantine | `Missing values in columns: {column_names}` |
| **Grade Bounds** | `G1`, `G2`, `G3` | `< 0` OR `> 20` | Reject & Quarantine | `Invalid {G} mark '{val}': must be between 0 and 20` |
| **Grade Type** | `G1`, `G2`, `G3` | Non-numeric string | Reject & Quarantine | `Invalid non-numeric value for {G}: '{val}'` |
| **Age Range** | `age` | `< 15` OR `> 25` | Reject & Quarantine | `Invalid age '{val}': must be between 15 and 25` |
| **Study Time Range** | `studytime` | Not in `[1, 2, 3, 4]` | Reject & Quarantine | `Invalid studytime '{val}': must be in {1, 2, 3, 4}` |
| **Failures Range** | `failures` | `< 0` OR `> 4` | Reject & Quarantine | `Invalid failures '{val}': must be between 0 and 4` |
| **Absence Non-negativity** | `absences` | `< 0` | Reject & Quarantine | `Invalid absences '{val}': cannot be negative` |
| **School Domain** | `school` | Not in `['GP', 'MS']` | Reject & Quarantine | `Invalid school '{val}': must be 'GP' or 'MS'` |
| **Gender Domain** | `sex` | Not in `['M', 'F']` | Reject & Quarantine | `Invalid gender '{val}': must be 'M' or 'F'` |
| **Address Domain** | `address` | Not in `['U', 'R']` | Reject & Quarantine | `Invalid address '{val}': must be 'U' or 'R'` |
| **Family Size Domain** | `famsize` | Not in `['LE3', 'GT3']` | Reject & Quarantine | `Invalid famsize '{val}': must be 'LE3' or 'GT3'` |
| **Parent Status Domain** | `Pstatus` | Not in `['T', 'A']` | Reject & Quarantine | `Invalid Pstatus '{val}': must be 'T' or 'A'` |
| **Duplicate Student** | `student_id` + `subject` | Duplicate composite key | Reject & Quarantine | `Duplicate student record for subject '{subject}'` |

---

## 3. Rejection Log Structure (`data/rejected/rejected_records.csv`)

When an incoming record violates any rule:
1. It is immediately diverted away from staging.
2. It is appended to `data/rejected/rejected_records.csv`.
3. Two audit columns are attached:
   - `rejection_reason`: Pipe-separated string of all rule violations triggered.
   - `rejected_at`: ISO 8601 UTC timestamp of the rejection event.

### Example Quarantined Row:
```csv
school,sex,age,address,famsize,Pstatus,Medu,Fedu,Mjob,Fjob,reason,guardian,traveltime,studytime,failures,schoolsup,famsup,paid,activities,nursery,higher,internet,romantic,famrel,freetime,goout,Dalc,Walc,health,absences,G1,G2,G3,subject,student_id,rejection_reason,rejected_at
GP,M,17,U,GT3,T,2,1,other,other,home,mother,1,1,3,no,yes,no,no,yes,yes,yes,no,5,4,5,1,2,5,0,5,0,0,Mathematics,STU-69668EB0,Duplicate student record for subject 'Mathematics',2026-09-08T11:10:08.824155+00:00
```

---

## 4. Ingestion Audit Log Structure (`data/raw/ingestion_audit.json`)

Tracks batch extraction metadata for regulatory and reproducibility compliance:
```json
{
  "source_file": "student-mat.csv",
  "source_path": "D:\\anura\\Documents\\mlops_project\\data\\raw\\student-mat.csv",
  "source_name": "UCI Student Performance - Mathematics",
  "extraction_date": "2026-09-08T11:11:47.530526+00:00",
  "row_count": 395,
  "column_count": 33,
  "columns": ["school", "sex", "age", ...],
  "delimiter": ";",
  "status": "SUCCESS"
}
```
