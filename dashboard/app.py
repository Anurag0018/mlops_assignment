"""
Streamlit Academic Analytics Dashboard
--------------------------------------
Interactive production-grade dashboard visualizing the 5 core analytical views:
1. Overall Performance (KPIs, Grade distributions, Categories)
2. Attendance vs Marks (Absence impact, Scatter correlation, Risk quartiles)
3. Subject Performance (Math vs Portuguese, G1->G2->G3 progression, Pass/Fail)
4. Demographic Analysis (Gender, Location, Parental Education, Internet access)
5. Student Profile & Risk Analyzer (Drill-down by Student ID, grade trajectory, intervention alerts)
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.database.load import query_analytics_data, get_db_engine

# Streamlit Page Setup
st.set_page_config(
    page_title="Student Performance Data Engineering Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E40AF;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-pass {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
    }
    .badge-fail {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:
    """Load analytical data mart cached for performance."""
    try:
        df = query_analytics_data()
        return df
    except Exception as e:
        st.error(f"Error loading analytical data: {e}")
        return pd.DataFrame()


def main():
    df_all = load_data()

    if df_all.empty:
        st.warning("⚠️ No data available in the analytical mart. Please run the ETL pipeline first:")
        st.code("python dags/student_pipeline.py", language="bash")
        return

    # Header
    st.markdown('<div class="main-title">🎓 Student Performance Data Engineering Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Part 1: End-to-End Ingestion, Validation, Transformation, PostgreSQL Storage & Analytics Mart</div>', unsafe_allow_html=True)

    # Sidebar Controls & Global Filters
    st.sidebar.image("https://img.icons8.com/fluency/96/education.png", width=70)
    st.sidebar.title("Pipeline Controls")
    
    # Database status banner
    _, is_pg = get_db_engine()
    db_badge = "🟢 PostgreSQL (Production)" if is_pg else "🟡 SQLite (Local Fallback)"
    st.sidebar.caption(f"**Database Backend:** {db_badge}")
    st.sidebar.divider()

    st.sidebar.subheader("Filter Analytical Mart")
    
    # Filter: Subject
    available_subjects = sorted(df_all["subject"].unique())
    selected_subjects = st.sidebar.multiselect(
        "Select Subjects",
        options=available_subjects,
        default=available_subjects
    )

    # Filter: School
    available_schools = sorted(df_all["school"].unique())
    school_labels = {"GP": "GP - Gabriel Pereira", "MS": "MS - Mousinho da Silveira"}
    selected_schools = st.sidebar.multiselect(
        "Select Schools",
        options=available_schools,
        format_func=lambda x: school_labels.get(x, x),
        default=available_schools
    )

    # Filter: Gender
    available_genders = sorted(df_all["sex"].unique())
    gender_labels = {"F": "Female (F)", "M": "Male (M)"}
    selected_genders = st.sidebar.multiselect(
        "Select Gender",
        options=available_genders,
        format_func=lambda x: gender_labels.get(x, x),
        default=available_genders
    )

    # Filter: Performance Category
    available_perf = ["Distinction", "Good", "Satisfactory", "At-Risk"]
    selected_perf = st.sidebar.multiselect(
        "Performance Tier",
        options=available_perf,
        default=available_perf
    )

    # Apply Filters
    df_filtered = df_all[
        (df_all["subject"].isin(selected_subjects if selected_subjects else available_subjects)) &
        (df_all["school"].isin(selected_schools if selected_schools else available_schools)) &
        (df_all["sex"].isin(selected_genders if selected_genders else available_genders)) &
        (df_all["performance_category"].isin(selected_perf if selected_perf else available_perf))
    ].copy()

    st.sidebar.caption(f"Displaying **{len(df_filtered)}** of **{len(df_all)}** enrollments")
    st.sidebar.divider()
    st.sidebar.info("💡 **Pipeline Info:**\n- Ingestion: Python/Pandas\n- Validation: Range 0-20 & Quarantining\n- Storage: Normalized PostgreSQL & OLAP Mart\n- Orchestration: Airflow DAG")

    # Main Tabbed Views (5 core dashboards)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 1. Overall Performance",
        "🕒 2. Attendance vs Marks",
        "📚 3. Subject Performance",
        "👥 4. Demographic Analysis",
        "🔍 5. Student Profile & Risk Analyzer"
    ])

    # =========================================================================
    # TAB 1: OVERALL PERFORMANCE
    # =========================================================================
    with tab1:
        st.subheader("Executive Academic Performance Summary")

        # Top KPI Metric Cards
        col1, col2, col3, col4, col5 = st.columns(5)
        
        unique_students = df_filtered["student_id"].nunique()
        avg_grade = df_filtered["average_grade"].mean()
        pass_rate = (df_filtered["pass_fail"] == "Pass").mean() * 100
        avg_absences = df_filtered["absences"].mean()
        avg_attendance = df_filtered["attendance_rate"].mean()

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Students</div>
                <div class="metric-value">{unique_students}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg Grade (0-20)</div>
                <div class="metric-value">{avg_grade:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Pass Rate</div>
                <div class="metric-value">{pass_rate:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg Absences</div>
                <div class="metric-value">{avg_absences:.1f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Attendance Rate</div>
                <div class="metric-value">{avg_attendance:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts Row
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # Distribution of Final Marks (G3)
            fig_hist = px.histogram(
                df_filtered,
                x="final_grade",
                color="pass_fail",
                color_discrete_map={"Pass": "#10B981", "Fail": "#EF4444"},
                nbins=21,
                title="Final Grade Distribution (G3: 0–20 Scale)",
                labels={"final_grade": "Final Mark (G3)", "count": "Student Count"}
            )
            fig_hist.add_vline(x=10, line_dash="dash", line_color="#DC2626", annotation_text="Passing Threshold (10)")
            fig_hist.update_layout(bargap=0.1, template="plotly_white")
            st.plotly_chart(fig_hist, use_container_width=True)

        with chart_col2:
            # Performance Category Donut Chart
            cat_counts = df_filtered["performance_category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            colors = {
                "Distinction": "#3B82F6",
                "Good": "#10B981",
                "Satisfactory": "#F59E0B",
                "At-Risk": "#EF4444"
            }
            fig_donut = px.pie(
                cat_counts,
                names="Category",
                values="Count",
                hole=0.45,
                color="Category",
                color_discrete_map=colors,
                title="Student Academic Classification"
            )
            fig_donut.update_layout(template="plotly_white")
            st.plotly_chart(fig_donut, use_container_width=True)

        # Data Mart Table Preview
        with st.expander("🔎 View Raw Analytical Data Mart Records"):
            st.dataframe(df_filtered.head(50), use_container_width=True)

    # =========================================================================
    # TAB 2: ATTENDANCE VS MARKS
    # =========================================================================
    with tab2:
        st.subheader("Impact of Attendance & School Absences on Academic Performance")

        col_att1, col_att2 = st.columns([3, 2])

        with col_att1:
            # Scatter Plot: Absences vs Average Grade
            fig_scatter = px.scatter(
                df_filtered,
                x="absences",
                y="average_grade",
                color="performance_category",
                color_discrete_map={
                    "Distinction": "#2563EB",
                    "Good": "#10B981",
                    "Satisfactory": "#F59E0B",
                    "At-Risk": "#EF4444"
                },
                title="Correlation: Absences vs Composite Grade",
                labels={"absences": "Number of Absences", "average_grade": "Average Grade (G1+G2+G3)/3"},
                hover_data=["student_id", "subject", "school"]
            )

            # Draw OLS linear regression line using NumPy (zero dependency on statsmodels)
            if len(df_filtered) > 1 and df_filtered["absences"].nunique() > 1:
                x_vals = df_filtered["absences"].astype(float).values
                y_vals = df_filtered["average_grade"].astype(float).values
                slope, intercept = np.polyfit(x_vals, y_vals, 1)
                x_trend = np.linspace(x_vals.min(), x_vals.max(), 50)
                y_trend = slope * x_trend + intercept
                fig_scatter.add_trace(
                    go.Scatter(
                        x=x_trend,
                        y=y_trend,
                        mode="lines",
                        name=f"Trendline (slope={slope:.2f})",
                        line=dict(color="#DC2626", dash="dash", width=2)
                    )
                )

            fig_scatter.update_layout(template="plotly_white")
            st.plotly_chart(fig_scatter, use_container_width=True)

        with col_att2:
            # Absence Tiers & Mean Performance Table
            df_tier = df_filtered.copy()
            df_tier["absence_tier"] = pd.cut(
                df_tier["absences"],
                bins=[-1, 0, 4, 10, 100],
                labels=["0 (Perfect)", "1-4 (Low)", "5-10 (Moderate)", ">10 (Chronic)"]
            )
            tier_summary = df_tier.groupby("absence_tier", observed=False).agg(
                students=("student_id", "count"),
                avg_grade=("average_grade", "mean"),
                pass_rate=("pass_fail", lambda x: (x == "Pass").mean() * 100)
            ).reset_index()

            tier_summary["avg_grade"] = tier_summary["avg_grade"].round(2)
            tier_summary["pass_rate"] = tier_summary["pass_rate"].round(1)

            st.markdown("#### Absence Tier Breakdown")
            st.dataframe(
                tier_summary.rename(columns={
                    "absence_tier": "Absence Tier",
                    "students": "Students",
                    "avg_grade": "Mean Grade",
                    "pass_rate": "Pass Rate (%)"
                }),
                use_container_width=True
            )

            # Boxplot of Grades by Absence Tier
            fig_box = px.box(
                df_tier,
                x="absence_tier",
                y="average_grade",
                color="absence_tier",
                title="Grade Variance across Absence Tiers",
                labels={"absence_tier": "Absence Tier", "average_grade": "Average Grade"}
            )
            fig_box.update_layout(showlegend=False, template="plotly_white")
            st.plotly_chart(fig_box, use_container_width=True)

    # =========================================================================
    # TAB 3: SUBJECT PERFORMANCE
    # =========================================================================
    with tab3:
        st.subheader("Subject-Level Comparative Analysis: Mathematics vs Portuguese")

        subj_metrics = df_filtered.groupby("subject").agg(
            total_students=("student_id", "count"),
            mean_g1=("g1", "mean"),
            mean_g2=("g2", "mean"),
            mean_g3=("g3", "mean"),
            mean_composite=("average_grade", "mean"),
            pass_rate=("pass_fail", lambda x: (x == "Pass").mean() * 100)
        ).reset_index().round(2)

        st.dataframe(
            subj_metrics.rename(columns={
                "subject": "Subject",
                "total_students": "Total Enrollments",
                "mean_g1": "Mean G1",
                "mean_g2": "Mean G2",
                "mean_g3": "Mean Final (G3)",
                "mean_composite": "Mean Composite",
                "pass_rate": "Pass Rate (%)"
            }),
            use_container_width=True
        )

        col_s1, col_s2 = st.columns(2)

        with col_s1:
            # Grade Progression: G1 -> G2 -> G3 by Subject
            progression_data = []
            for subj in df_filtered["subject"].unique():
                sub_df = df_filtered[df_filtered["subject"] == subj]
                progression_data.append({"Subject": subj, "Period": "G1 (Period 1)", "Grade": sub_df["g1"].mean()})
                progression_data.append({"Subject": subj, "Period": "G2 (Period 2)", "Grade": sub_df["g2"].mean()})
                progression_data.append({"Subject": subj, "Period": "G3 (Final)", "Grade": sub_df["g3"].mean()})
            
            prog_df = pd.DataFrame(progression_data)
            fig_prog = px.line(
                prog_df,
                x="Period",
                y="Grade",
                color="Subject",
                markers=True,
                title="Grade Trajectory: Period 1 (G1) → Period 2 (G2) → Final (G3)"
            )
            fig_prog.update_layout(template="plotly_white", yaxis_range=[0, 20])
            st.plotly_chart(fig_prog, use_container_width=True)

        with col_s2:
            # Pass vs Fail Ratios by Subject
            pf_df = df_filtered.groupby(["subject", "pass_fail"]).size().reset_index(name="count")
            fig_pf = px.bar(
                pf_df,
                x="subject",
                y="count",
                color="pass_fail",
                barmode="group",
                color_discrete_map={"Pass": "#10B981", "Fail": "#EF4444"},
                title="Pass vs Fail Distribution by Course"
            )
            fig_pf.update_layout(template="plotly_white")
            st.plotly_chart(fig_pf, use_container_width=True)

    # =========================================================================
    # TAB 4: DEMOGRAPHIC ANALYSIS
    # =========================================================================
    with tab4:
        st.subheader("Socio-Demographic Indicators & Academic Success")

        col_d1, col_d2 = st.columns(2)

        with col_d1:
            # Parental Education vs Final Grade
            edu_order = ["None", "Primary (4th grade)", "5th to 9th grade", "Secondary Education", "Higher Education"]
            fig_edu = px.bar(
                df_filtered.groupby("parent_education", observed=False)["average_grade"].mean().reindex(edu_order).reset_index(),
                x="parent_education",
                y="average_grade",
                color="average_grade",
                color_continuous_scale="Blues",
                title="Average Grade by Highest Parental Education Level",
                labels={"parent_education": "Parent Education Level", "average_grade": "Mean Grade"}
            )
            fig_edu.update_layout(template="plotly_white", xaxis_tickangle=-25)
            st.plotly_chart(fig_edu, use_container_width=True)

        with col_d2:
            # Study Time Category vs Performance
            study_order = ["<2 hours", "2 to 5 hours", "5 to 10 hours", ">10 hours"]
            fig_study = px.box(
                df_filtered,
                x="study_time_category",
                y="final_grade",
                category_orders={"study_time_category": study_order},
                color="study_time_category",
                title="Impact of Weekly Study Time on Final Grade (G3)",
                labels={"study_time_category": "Study Time", "final_grade": "Final Mark"}
            )
            fig_study.update_layout(showlegend=False, template="plotly_white")
            st.plotly_chart(fig_study, use_container_width=True)

        col_d3, col_d4 = st.columns(2)

        with col_d3:
            # Gender vs Average Grade by Subject
            gender_df = df_filtered.groupby(["subject", "sex"])["average_grade"].mean().reset_index()
            gender_df["sex_label"] = gender_df["sex"].map({"F": "Female", "M": "Male"})
            fig_gender = px.bar(
                gender_df,
                x="subject",
                y="average_grade",
                color="sex_label",
                barmode="group",
                color_discrete_map={"Female": "#EC4899", "Male": "#3B82F6"},
                title="Gender Performance Comparison across Subjects"
            )
            fig_gender.update_layout(template="plotly_white")
            st.plotly_chart(fig_gender, use_container_width=True)

        with col_d4:
            # Urban vs Rural Address Performance
            addr_df = df_filtered.groupby("address")["final_grade"].mean().reset_index()
            addr_df["address_label"] = addr_df["address"].map({"U": "Urban", "R": "Rural"})
            fig_addr = px.pie(
                addr_df,
                names="address_label",
                values="final_grade",
                hole=0.4,
                title="Average Performance: Urban vs Rural Students"
            )
            fig_addr.update_layout(template="plotly_white")
            st.plotly_chart(fig_addr, use_container_width=True)

    # =========================================================================
    # TAB 5: STUDENT PROFILE & RISK ANALYZER
    # =========================================================================
    with tab5:
        st.subheader("Individual Student Profile & At-Risk Diagnostic")

        # Student Selector
        all_students = sorted(df_filtered["student_id"].unique())
        if not all_students:
            st.info("No students found with current filters.")
            return

        selected_student_id = st.selectbox(
            "Search / Select Student Identifier:",
            options=all_students,
            index=0
        )

        stu_records = df_filtered[df_filtered["student_id"] == selected_student_id]
        primary_record = stu_records.iloc[0]

        # Profile Card
        st.markdown("### Student Dossier")
        card_col1, card_col2, card_col3, card_col4 = st.columns(4)

        with card_col1:
            st.markdown(f"**Student ID:** `{primary_record['student_id']}`")
            st.markdown(f"**School:** {school_labels.get(primary_record['school'], primary_record['school'])}")
            st.markdown(f"**Age:** {primary_record['age']} years")
        with card_col2:
            st.markdown(f"**Gender:** {'Female' if primary_record['sex'] == 'F' else 'Male'}")
            st.markdown(f"**Location:** {'Urban' if primary_record['address'] == 'U' else 'Rural'}")
            st.markdown(f"**Parent Education:** {primary_record['parent_education']}")
        with card_col3:
            st.markdown(f"**Weekly Study Time:** {primary_record['study_time_category']}")
            st.markdown(f"**Total Absences:** {stu_records['absences'].sum()}")
            st.markdown(f"**Past Failures:** {primary_record['failures']}")
        with card_col4:
            risk = primary_record["risk_status"]
            if risk == "High Risk":
                st.error(f"🚨 **Status: {risk}**")
            elif risk == "Medium Risk":
                st.warning(f"⚠️ **Status: {risk}**")
            else:
                st.success(f"✅ **Status: {risk}**")

        st.divider()

        # Subject Courses Taken by This Student
        st.markdown("#### Course Enrollments & Grade Breakdown")
        
        display_cols = ["subject", "g1", "g2", "g3", "average_grade", "pass_fail", "performance_category", "grade_improvement", "absences"]
        st.dataframe(stu_records[display_cols].rename(columns={
            "subject": "Course Subject",
            "g1": "Period 1 (G1)",
            "g2": "Period 2 (G2)",
            "g3": "Final Mark (G3)",
            "average_grade": "Composite Avg",
            "pass_fail": "Pass/Fail",
            "performance_category": "Performance Tier",
            "grade_improvement": "Trajectory (G3-G1)",
            "absences": "Absences"
        }), use_container_width=True)

        # Trajectory Visualization for the Student
        traj_data = []
        for _, rec in stu_records.iterrows():
            traj_data.append({"Course": rec["subject"], "Period": "G1", "Mark": rec["g1"]})
            traj_data.append({"Course": rec["subject"], "Period": "G2", "Mark": rec["g2"]})
            traj_data.append({"Course": rec["subject"], "Period": "G3", "Mark": rec["g3"]})
        
        fig_stu_traj = px.line(
            pd.DataFrame(traj_data),
            x="Period",
            y="Mark",
            color="Course",
            markers=True,
            title=f"Grade Evolution for Student {selected_student_id}"
        )
        fig_stu_traj.update_layout(template="plotly_white", yaxis_range=[0, 20])
        st.plotly_chart(fig_stu_traj, use_container_width=True)

        # Targeted Academic Recommendations
        st.markdown("#### Recommended Interventions")
        if primary_record["risk_status"] == "High Risk":
            st.error("• **Mandatory Tutoring:** Student has failing marks and prior class failures. Enroll in subject support sessions immediately.\n• **Attendance Counseling:** Notify guardian regarding chronic absences.")
        elif primary_record["risk_status"] == "Medium Risk":
            st.warning("• **Academic Check-in:** Student is near the passing threshold. Schedule bi-weekly mentor review.\n• **Study Skills Workshop:** Encourage increasing weekly study time above 5 hours.")
        else:
            st.success("• **Enrichment Program:** Student is performing well on all indicators. Candidate for advanced placement or peer mentoring.")


if __name__ == "__main__":
    main()
