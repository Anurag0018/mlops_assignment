# Data Dictionary: Student Performance Data Pipeline

This document defines the schema, types, descriptions, domain constraints, and validation rules for all fields ingested, staged, transformed, and stored in the PostgreSQL analytical data mart.

---

## 1. Demographic & Family Background Attributes (`students` Dimension)

| Column Name | SQL Type | Description | Domain / Valid Values | Validation Rule | Example |
|---|---|---|---|---|---|
| `student_id` | `VARCHAR(50)` | Deterministic unique student identifier | Hash of demographic composite key | Unique Primary Key, Non-null | `STU-69668EB0` |
| `school` | `VARCHAR(10)` | Student's school | `'GP'` (Gabriel Pereira), `'MS'` (Mousinho da Silveira) | Must be in `{'GP', 'MS'}` | `'GP'` |
| `sex` | `VARCHAR(5)` | Student's biological sex | `'F'` (Female), `'M'` (Male) | Must be in `{'F', 'M'}` | `'F'` |
| `age` | `INT` | Student's age in years | Integer between 15 and 22 (max 25) | `15 <= age <= 25` | `17` |
| `address` | `VARCHAR(5)` | Student's home address type | `'U'` (Urban), `'R'` (Rural) | Must be in `{'U', 'R'}` | `'U'` |
| `famsize` | `VARCHAR(10)` | Family size | `'LE3'` ($\le 3$), `'GT3'` ($> 3$) | Must be in `{'LE3', 'GT3'}` | `'GT3'` |
| `pstatus` | `VARCHAR(5)` | Parent cohabitation status | `'T'` (Together), `'A'` (Apart) | Must be in `{'T', 'A'}` | `'T'` |
| `medu` | `INT` | Mother's education level | 0: None, 1: Primary (4th grade), 2: 5th-9th grade, 3: Secondary, 4: Higher education | `0 <= medu <= 4` | `4` |
| `fedu` | `INT` | Father's education level | 0: None, 1: Primary (4th grade), 2: 5th-9th grade, 3: Secondary, 4: Higher education | `0 <= fedu <= 4` | `3` |
| `mjob` | `VARCHAR(50)` | Mother's job | `'teacher'`, `'health'`, `'services'`, `'at_home'`, `'other'` | Non-null string | `'services'` |
| `fjob` | `VARCHAR(50)` | Father's job | `'teacher'`, `'health'`, `'services'`, `'at_home'`, `'other'` | Non-null string | `'other'` |
| `reason` | `VARCHAR(50)` | Reason to choose this school | `'home'`, `'reputation'`, `'course'`, `'other'` | Non-null string | `'course'` |
| `guardian` | `VARCHAR(50)` | Student's legal guardian | `'mother'`, `'father'`, `'other'` | Non-null string | `'mother'` |
| `parent_education` | `VARCHAR(50)` | Highest parental education tier (Engineered) | `'None'`, `'Primary (4th grade)'`, `'5th to 9th grade'`, `'Secondary Education'`, `'Higher Education'` | Derived from `max(medu, fedu)` | `'Higher Education'` |

---

## 2. Academic Performance & Study Habits (`academic_performance` Fact)

| Column Name | SQL Type | Description | Domain / Valid Values | Validation Rule | Example |
|---|---|---|---|---|---|
| `record_id` | `SERIAL / INT` | Autoincrement surrogate primary key | Integer | Primary Key | `1` |
| `student_id` | `VARCHAR(50)` | Foreign key referencing `students.student_id` | Matches `students` | Foreign Key, Non-null | `STU-69668EB0` |
| `subject` | `VARCHAR(20)` | Course subject name | `'Mathematics'`, `'Portuguese'` | Must be in `{'Mathematics', 'Portuguese'}` | `'Mathematics'` |
| `studytime` | `INT` | Weekly study time category | 1: $<2$ hrs, 2: 2–5 hrs, 3: 5–10 hrs, 4: $>10$ hrs | `1 <= studytime <= 4` | `2` |
| `study_time_category` | `VARCHAR(50)` | Readable weekly study bucket (Engineered) | `'<2 hours'`, `'2 to 5 hours'`, `'5 to 10 hours'`, `'>10 hours'` | Derived mapping | `'2 to 5 hours'` |
| `failures` | `INT` | Number of past class failures | 0 to 4 | `0 <= failures <= 4` | `0` |
| `schoolsup` | `VARCHAR(5)` | Extra educational school support | `'yes'`, `'no'` | In `{'yes', 'no'}` | `'no'` |
| `famsup` | `VARCHAR(5)` | Family educational support | `'yes'`, `'no'` | In `{'yes', 'no'}` | `'yes'` |
| `paid` | `VARCHAR(5)` | Extra paid classes within the course subject | `'yes'`, `'no'` | In `{'yes', 'no'}` | `'no'` |
| `activities` | `VARCHAR(5)` | Extra-curricular activities | `'yes'`, `'no'` | In `{'yes', 'no'}` | `'yes'` |
| `nursery` | `VARCHAR(5)` | Attended nursery school | `'yes'`, `'no'` | In `{'yes', 'no'}` | `'yes'` |
| `higher` | `VARCHAR(5)` | Wants to take higher education | `'yes'`, `'no'` | In `{'yes', 'no'}` | `'yes'` |
| `internet` | `VARCHAR(5)` | Internet access at home | `'yes'`, `'no'` | In `{'yes', 'no'}` | `'yes'` |
| `romantic` | `VARCHAR(5)` | In a romantic relationship | `'yes'`, `'no'` | In `{'yes', 'no'}` | `'no'` |
| `famrel` | `INT` | Quality of family relationships | 1 (very bad) to 5 (excellent) | `1 <= famrel <= 5` | `4` |
| `freetime` | `INT` | Free time after school | 1 (very low) to 5 (very high) | `1 <= freetime <= 5` | `3` |
| `goout` | `INT` | Going out with friends | 1 (very low) to 5 (very high) | `1 <= goout <= 5` | `3` |
| `dalc` | `INT` | Workday alcohol consumption | 1 (very low) to 5 (very high) | `1 <= dalc <= 5` | `1` |
| `walc` | `INT` | Weekend alcohol consumption | 1 (very low) to 5 (very high) | `1 <= walc <= 5` | `2` |
| `health` | `INT` | Current health status | 1 (very bad) to 5 (very good) | `1 <= health <= 5` | `4` |
| `absences` | `INT` | Number of school absences | 0 to 93 | `absences >= 0` | `4` |
| `attendance_rate` | `NUMERIC(5,2)` | Computed attendance percentage (Engineered) | $0.00\%$ to $100.00\%$ | $100 \times \max(0, 1 - absences/93)$ | `95.70` |
| `g1` | `INT` | First period grade | 0 to 20 | `0 <= g1 <= 20` | `12` |
| `g2` | `INT` | Second period grade | 0 to 20 | `0 <= g2 <= 20` | `14` |
| `g3` | `INT` | Final grade (Target variable) | 0 to 20 | `0 <= g3 <= 20` | `15` |

---

## 3. Analytical Data Mart & Feature Engineered Fields (`student_analytics`)

| Field Name | Type | Formula / Logic | Business Meaning |
|---|---|---|---|
| `average_grade` | `NUMERIC(5,2)` | `(g1 + g2 + g3) / 3.0` | Overall composite grade across all 3 evaluation periods |
| `final_grade` | `INT` | `g3` | Official final academic mark |
| `pass_fail` | `VARCHAR(10)` | `CASE WHEN g3 >= 10 THEN 'Pass' ELSE 'Fail'` | Standard academic pass/fail threshold (10 out of 20) |
| `performance_category` | `VARCHAR(20)` | `g3 >= 16 -> 'Distinction'`, `g3 >= 14 -> 'Good'`, `g3 >= 10 -> 'Satisfactory'`, `else -> 'At-Risk'` | Tiered academic performance classification |
| `grade_improvement` | `INT` | `g3 - g1` | Grade progression/trajectory from period 1 to final |
| `risk_status` | `VARCHAR(20)` | `High Risk` if $g3 < 10$ and ($failures > 0$ or $absences > 10$), `Medium Risk` if $g3 < 10$ or $failures > 0$ or $absences > 10$, else `Low Risk` | Proactive early warning flag for educational interventions |
