-- ==============================================================================
-- Schema Definition: Student Performance Data Pipeline
-- PostgreSQL Dialect (compatible with standard relational databases)
-- ==============================================================================

-- Drop tables if they exist in reverse dependency order
DROP TABLE IF EXISTS student_analytics CASCADE;
DROP TABLE IF EXISTS academic_performance CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS ingestion_audit CASCADE;

-- ------------------------------------------------------------------------------
-- 1. Ingestion Audit Table
-- Tracks metadata for raw extractions
-- ------------------------------------------------------------------------------
CREATE TABLE ingestion_audit (
    audit_id SERIAL PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL,
    extraction_date TIMESTAMP NOT NULL,
    row_count INT NOT NULL,
    column_count INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 2. Students Dimension Table
-- Stores demographic, home background, and parental indicators
-- ------------------------------------------------------------------------------
CREATE TABLE students (
    student_id VARCHAR(50) PRIMARY KEY,
    school VARCHAR(10) NOT NULL CHECK (school IN ('GP', 'MS')),
    sex VARCHAR(5) NOT NULL CHECK (sex IN ('M', 'F')),
    age INT NOT NULL CHECK (age BETWEEN 15 AND 25),
    address VARCHAR(5) NOT NULL CHECK (address IN ('U', 'R')),
    famsize VARCHAR(10) NOT NULL CHECK (famsize IN ('LE3', 'GT3')),
    pstatus VARCHAR(5) NOT NULL CHECK (pstatus IN ('T', 'A')),
    medu INT NOT NULL CHECK (medu BETWEEN 0 AND 4),
    fedu INT NOT NULL CHECK (fedu BETWEEN 0 AND 4),
    mjob VARCHAR(50) NOT NULL,
    fjob VARCHAR(50) NOT NULL,
    reason VARCHAR(50) NOT NULL,
    guardian VARCHAR(50) NOT NULL,
    parent_education VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 3. Academic Performance Fact Table
-- Stores course-level performance, study habits, health, and marks
-- ------------------------------------------------------------------------------
CREATE TABLE academic_performance (
    record_id SERIAL PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    subject VARCHAR(20) NOT NULL CHECK (subject IN ('Mathematics', 'Portuguese')),
    studytime INT NOT NULL CHECK (studytime BETWEEN 1 AND 4),
    study_time_category VARCHAR(50),
    failures INT NOT NULL CHECK (failures >= 0),
    schoolsup VARCHAR(5) NOT NULL CHECK (schoolsup IN ('yes', 'no')),
    famsup VARCHAR(5) NOT NULL CHECK (famsup IN ('yes', 'no')),
    paid VARCHAR(5) NOT NULL CHECK (paid IN ('yes', 'no')),
    activities VARCHAR(5) NOT NULL CHECK (activities IN ('yes', 'no')),
    nursery VARCHAR(5) NOT NULL CHECK (nursery IN ('yes', 'no')),
    higher VARCHAR(5) NOT NULL CHECK (higher IN ('yes', 'no')),
    internet VARCHAR(5) NOT NULL CHECK (internet IN ('yes', 'no')),
    romantic VARCHAR(5) NOT NULL CHECK (romantic IN ('yes', 'no')),
    famrel INT NOT NULL CHECK (famrel BETWEEN 1 AND 5),
    freetime INT NOT NULL CHECK (freetime BETWEEN 1 AND 5),
    goout INT NOT NULL CHECK (goout BETWEEN 1 AND 5),
    dalc INT NOT NULL CHECK (dalc BETWEEN 1 AND 5),
    walc INT NOT NULL CHECK (walc BETWEEN 1 AND 5),
    health INT NOT NULL CHECK (health BETWEEN 1 AND 5),
    absences INT NOT NULL CHECK (absences >= 0),
    attendance_rate NUMERIC(5, 2) CHECK (attendance_rate BETWEEN 0 AND 100),
    g1 INT NOT NULL CHECK (g1 BETWEEN 0 AND 20),
    g2 INT NOT NULL CHECK (g2 BETWEEN 0 AND 20),
    g3 INT NOT NULL CHECK (g3 BETWEEN 0 AND 20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_subject UNIQUE (student_id, subject)
);

-- ------------------------------------------------------------------------------
-- 4. Indexes for Optimal Query Performance
-- ------------------------------------------------------------------------------
CREATE INDEX idx_students_school ON students(school);
CREATE INDEX idx_students_sex ON students(sex);
CREATE INDEX idx_academic_student ON academic_performance(student_id);
CREATE INDEX idx_academic_subject ON academic_performance(subject);
CREATE INDEX idx_academic_g3 ON academic_performance(g3);
