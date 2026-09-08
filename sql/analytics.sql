-- ==============================================================================
-- Analytics Layer & Data Mart Definition: Student Performance Pipeline
-- PostgreSQL Dialect
-- ==============================================================================

-- Drop existing views and mart if they exist
DROP VIEW IF EXISTS vw_at_risk_students CASCADE;
DROP VIEW IF EXISTS vw_demographic_performance CASCADE;
DROP VIEW IF EXISTS vw_attendance_impact CASCADE;
DROP VIEW IF EXISTS vw_subject_summary CASCADE;
DROP VIEW IF EXISTS vw_overall_kpis CASCADE;
DROP TABLE IF EXISTS student_analytics CASCADE;

-- ------------------------------------------------------------------------------
-- 1. Student Analytics Data Mart (Denormalized OLAP Table)
-- ------------------------------------------------------------------------------
CREATE TABLE student_analytics (
    analytics_id SERIAL PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL,
    school VARCHAR(10) NOT NULL,
    sex VARCHAR(5) NOT NULL,
    age INT NOT NULL,
    address VARCHAR(5) NOT NULL,
    famsize VARCHAR(10) NOT NULL,
    pstatus VARCHAR(5) NOT NULL,
    parent_education VARCHAR(50),
    mjob VARCHAR(50),
    fjob VARCHAR(50),
    subject VARCHAR(20) NOT NULL,
    studytime INT NOT NULL,
    study_time_category VARCHAR(50),
    failures INT NOT NULL,
    absences INT NOT NULL,
    attendance_rate NUMERIC(5, 2),
    g1 INT NOT NULL,
    g2 INT NOT NULL,
    g3 INT NOT NULL,
    average_grade NUMERIC(5, 2) NOT NULL,
    final_grade INT NOT NULL,
    pass_fail VARCHAR(10) NOT NULL CHECK (pass_fail IN ('Pass', 'Fail')),
    performance_category VARCHAR(20) NOT NULL CHECK (performance_category IN ('Distinction', 'Good', 'Satisfactory', 'At-Risk')),
    grade_improvement INT NOT NULL,
    risk_status VARCHAR(20) NOT NULL CHECK (risk_status IN ('High Risk', 'Medium Risk', 'Low Risk')),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analytics_student ON student_analytics(student_id);
CREATE INDEX idx_analytics_subject ON student_analytics(subject);
CREATE INDEX idx_analytics_perf_cat ON student_analytics(performance_category);
CREATE INDEX idx_analytics_pass_fail ON student_analytics(pass_fail);
CREATE INDEX idx_analytics_risk ON student_analytics(risk_status);

-- ------------------------------------------------------------------------------
-- 2. Populate Mart Query (Used during ELT / Refresh)
-- ------------------------------------------------------------------------------
INSERT INTO student_analytics (
    student_id, school, sex, age, address, famsize, pstatus, parent_education,
    mjob, fjob, subject, studytime, study_time_category, failures, absences,
    attendance_rate, g1, g2, g3, average_grade, final_grade, pass_fail,
    performance_category, grade_improvement, risk_status
)
SELECT 
    s.student_id,
    s.school,
    s.sex,
    s.age,
    s.address,
    s.famsize,
    s.pstatus,
    s.parent_education,
    s.mjob,
    s.fjob,
    a.subject,
    a.studytime,
    a.study_time_category,
    a.failures,
    a.absences,
    a.attendance_rate,
    a.g1,
    a.g2,
    a.g3,
    ROUND((a.g1 + a.g2 + a.g3)::NUMERIC / 3.0, 2) AS average_grade,
    a.g3 AS final_grade,
    CASE WHEN a.g3 >= 10 THEN 'Pass' ELSE 'Fail' END AS pass_fail,
    CASE 
        WHEN a.g3 >= 16 THEN 'Distinction'
        WHEN a.g3 >= 14 THEN 'Good'
        WHEN a.g3 >= 10 THEN 'Satisfactory'
        ELSE 'At-Risk'
    END AS performance_category,
    (a.g3 - a.g1) AS grade_improvement,
    CASE 
        WHEN a.g3 < 10 AND (a.failures > 0 OR a.absences > 10) THEN 'High Risk'
        WHEN a.g3 < 10 OR a.failures > 0 OR a.absences > 10 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS risk_status
FROM students s
JOIN academic_performance a ON s.student_id = a.student_id;

-- ------------------------------------------------------------------------------
-- 3. Analytical Views
-- ------------------------------------------------------------------------------

-- View: Overall KPI Summary
CREATE VIEW vw_overall_kpis AS
SELECT 
    COUNT(DISTINCT student_id) AS total_unique_students,
    COUNT(*) AS total_enrollments,
    ROUND(AVG(average_grade), 2) AS overall_avg_grade,
    ROUND(AVG(final_grade), 2) AS overall_final_grade,
    ROUND((SUM(CASE WHEN pass_fail = 'Pass' THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100.0, 2) AS overall_pass_rate_pct,
    ROUND(AVG(absences), 1) AS overall_avg_absences,
    ROUND(AVG(attendance_rate), 2) AS overall_avg_attendance_rate
FROM student_analytics;

-- View: Subject Summary
CREATE VIEW vw_subject_summary AS
SELECT 
    subject,
    COUNT(*) AS total_students,
    ROUND(AVG(average_grade), 2) AS avg_composite_grade,
    ROUND(AVG(final_grade), 2) AS avg_final_grade,
    ROUND((SUM(CASE WHEN pass_fail = 'Pass' THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100.0, 2) AS pass_rate_pct,
    ROUND(AVG(absences), 1) AS avg_absences,
    ROUND(AVG(attendance_rate), 2) AS avg_attendance_rate
FROM student_analytics
GROUP BY subject;

-- View: Attendance Impact on Performance
CREATE VIEW vw_attendance_impact AS
SELECT 
    CASE 
        WHEN absences = 0 THEN '0 (Perfect)'
        WHEN absences BETWEEN 1 AND 4 THEN '1-4 (Low)'
        WHEN absences BETWEEN 5 AND 10 THEN '5-10 (Moderate)'
        ELSE '>10 (High)'
    END AS absence_tier,
    COUNT(*) AS student_count,
    ROUND(AVG(average_grade), 2) AS avg_grade,
    ROUND(AVG(final_grade), 2) AS avg_final_grade,
    ROUND((SUM(CASE WHEN pass_fail = 'Pass' THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100.0, 2) AS pass_rate_pct
FROM student_analytics
GROUP BY 1
ORDER BY avg_grade DESC;

-- View: Demographic Performance Analysis
CREATE VIEW vw_demographic_performance AS
SELECT 
    sex,
    address,
    parent_education,
    COUNT(*) AS student_count,
    ROUND(AVG(final_grade), 2) AS avg_final_grade,
    ROUND((SUM(CASE WHEN pass_fail = 'Pass' THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100.0, 2) AS pass_rate_pct
FROM student_analytics
GROUP BY sex, address, parent_education
ORDER BY avg_final_grade DESC;

-- View: At-Risk Students Directory
CREATE VIEW vw_at_risk_students AS
SELECT 
    student_id,
    school,
    subject,
    age,
    absences,
    failures,
    g1,
    g2,
    g3 AS final_grade,
    average_grade,
    risk_status
FROM student_analytics
WHERE risk_status IN ('High Risk', 'Medium Risk')
ORDER BY g3 ASC, absences DESC;
