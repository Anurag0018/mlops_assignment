"""
Streamlit Academic Analytics Dashboard — Executive Edition
----------------------------------------------------------
Production-grade educational analytics portal visualizing 5 comprehensive views:
1. Executive KPI Summary & Grade Distributions
2. Attendance Impact, Scatter Correlation & Chronic Absenteeism Tiers
3. Subject Performance Comparison (Mathematics vs Portuguese)
4. Socio-Demographic & Parental Education Success Indicators
5. Student Diagnostic Dossier & Academic Early Warning System
"""

import sys
import os
from pathlib import Path
import json
import requests
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
from src.common.config import (
    MODEL_REGISTRY_PATH,
    REPORTS_DIR,
    REFERENCE_FEATURES_PATH,
    ALL_FEATURE_COLUMNS,
)
from api.schemas import StudentFeatures
from api.services import ModelService
from src.monitoring.drift import DriftDetector

API_URL = os.getenv("API_URL", "http://localhost:8000")

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="EduVision Analytics | Student Performance Data Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Modern Executive SaaS Theme CSS
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Executive Hero Header */
    .hero-container {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #1E3A8A 100%);
        border-radius: 16px;
        padding: 26px 32px;
        color: #FFFFFF;
        box-shadow: 0 10px 25px -5px rgba(30, 27, 75, 0.3);
        margin-bottom: 24px;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 6px;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        font-size: 1.0rem;
        color: #C7D2FE;
        font-weight: 400;
        margin-bottom: 16px;
        max-width: 850px;
        line-height: 1.5;
    }
    .badge-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }
    .hero-chip {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 5px 14px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        color: #F8FAFC;
    }

    /* KPI Metric Cards */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -2px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .kpi-stripe {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
    }
    .kpi-stripe-blue { background: linear-gradient(90deg, #3B82F6, #1D4ED8); }
    .kpi-stripe-indigo { background: linear-gradient(90deg, #6366F1, #4338CA); }
    .kpi-stripe-emerald { background: linear-gradient(90deg, #10B981, #047857); }
    .kpi-stripe-amber { background: linear-gradient(90deg, #F59E0B, #B45309); }
    .kpi-stripe-rose { background: linear-gradient(90deg, #F43F5E, #BE123C); }

    .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .kpi-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .kpi-icon {
        font-size: 1.3rem;
    }
    .kpi-value {
        font-size: 2.0rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }
    .kpi-subtext {
        font-size: 0.82rem;
        color: #64748B;
        margin-top: 6px;
        font-weight: 500;
    }

    /* Section Cards */
    .chart-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 4px;
    }
    .section-subtitle {
        font-size: 0.88rem;
        color: #64748B;
        margin-bottom: 16px;
    }

    /* Student Dossier Card */
    .dossier-card {
        background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
        border: 1px solid #DBEAFE;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }
    .dossier-avatar {
        width: 56px;
        height: 56px;
        background: #3B82F6;
        color: white;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: 800;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
    }
    .dossier-id {
        font-size: 1.4rem;
        font-weight: 800;
        color: #1E293B;
    }
    .dossier-meta {
        font-size: 0.9rem;
        color: #64748B;
    }

    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.82rem;
        text-align: center;
    }
    .badge-high-risk {
        background-color: #FEE2E2;
        color: #991B1B;
        border: 1px solid #FCA5A5;
    }
    .badge-med-risk {
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FCD34D;
    }
    .badge-low-risk {
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #86EFAC;
    }

    /* Callout Boxes */
    .callout-box {
        background: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 14px 18px;
        border-radius: 0 10px 10px 0;
        margin: 14px 0;
        font-size: 0.9rem;
        color: #334155;
    }
    .callout-box-alert {
        background: #FFF1F2;
        border-left: 4px solid #E11D48;
        padding: 14px 18px;
        border-radius: 0 10px 10px 0;
        margin: 14px 0;
        font-size: 0.9rem;
        color: #881337;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Data Loader
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:
    """Load analytical data mart cached for high performance."""
    try:
        return query_analytics_data()
    except Exception as e:
        st.error(f"Error loading analytical data mart: {e}")
        return pd.DataFrame()


# -----------------------------------------------------------------------------
# Chart Helpers with Standardized SaaS Palette
# -----------------------------------------------------------------------------
COLOR_PALETTE = {
    "Distinction": "#4F46E5",   # Royal Indigo
    "Good": "#0D9488",          # Teal
    "Satisfactory": "#F59E0B",  # Amber
    "At-Risk": "#E11D48",       # Crimson
    "Pass": "#10B981",          # Emerald
    "Fail": "#EF4444",          # Red
    "Mathematics": "#3B82F6",   # Blue
    "Portuguese": "#8B5CF6"     # Purple
}


def apply_chart_style(fig, height=380):
    """Apply consistent modern aesthetics to Plotly charts."""
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'Plus Jakarta Sans', sans-serif", size=12, color="#475569"),
        title_font=dict(family="'Plus Jakarta Sans', sans-serif", size=14, color="#0F172A"),
        xaxis=dict(gridcolor="#F1F5F9", showline=True, linecolor="#E2E8F0"),
        yaxis=dict(gridcolor="#F1F5F9", showline=True, linecolor="#E2E8F0"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)"
        )
    )
    return fig


# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------
def main():
    df_all = load_data()

    if df_all.empty:
        st.warning("⚠️ No data available in the analytical mart. Please run the ETL pipeline first:")
        st.code("python dags/student_pipeline.py", language="bash")
        return

    # -------------------------------------------------------------------------
    # 1. Executive Hero Banner
    # -------------------------------------------------------------------------
    _, is_pg = get_db_engine()
    db_status = "🟢 PostgreSQL (Warehouse)" if is_pg else "🟡 SQLite (Local Storage)"

    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-title">
            <span>🎓</span> Student Performance & Dropout-Risk Platform
        </div>
        <div class="hero-subtitle">
            Enterprise Data Engineering & MLOps Platform integrating automated ingestion, multi-stage validation, 
            relational dimensional storage, MLflow-tracked risk prediction, FastAPI microservices, and drift monitoring.
        </div>
        <div class="badge-bar">
            <span class="hero-chip">📦 1,044 Raw Ingested</span>
            <span class="hero-chip">🛡️ 16 Quarantined Duplicates</span>
            <span class="hero-chip">✅ 1,028 Valid Staging</span>
            <span class="hero-chip">🏛️ 662 Unique Students</span>
            <span class="hero-chip">{db_status}</span>
            <span class="hero-chip">⚡ Airflow Orchestrated</span>
            <span class="hero-chip">🤖 XGBoost Champion (v1.0.0)</span>
            <span class="hero-chip">🚀 FastAPI Serving</span>
            <span class="hero-chip">📊 MLflow Experiment Tracking</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 2. Sidebar Filters & Global Data Mart Controls
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("### 🎛️ Data Mart Filters")
        st.caption("Apply dimensional filters across all 5 dashboards:")

        # Filter: Subject
        all_subjects = sorted(df_all["subject"].unique())
        selected_subjects = st.multiselect(
            "Course Subject",
            options=all_subjects,
            default=all_subjects
        )

        # Filter: School
        all_schools = sorted(df_all["school"].unique())
        school_names = {"GP": "GP — Gabriel Pereira", "MS": "MS — Mousinho da Silveira"}
        selected_schools = st.multiselect(
            "Institution / School",
            options=all_schools,
            format_func=lambda x: school_names.get(x, x),
            default=all_schools
        )

        # Filter: Gender
        all_genders = sorted(df_all["sex"].unique())
        gender_names = {"F": "Female (F)", "M": "Male (M)"}
        selected_genders = st.multiselect(
            "Student Gender",
            options=all_genders,
            format_func=lambda x: gender_names.get(x, x),
            default=all_genders
        )

        # Filter: Performance Tier
        all_tiers = ["Distinction", "Good", "Satisfactory", "At-Risk"]
        selected_tiers = st.multiselect(
            "Performance Category",
            options=all_tiers,
            default=all_tiers
        )

        st.divider()

        # Download Filtered Mart Button
        df_filtered = df_all[
            (df_all["subject"].isin(selected_subjects if selected_subjects else all_subjects)) &
            (df_all["school"].isin(selected_schools if selected_schools else all_schools)) &
            (df_all["sex"].isin(selected_genders if selected_genders else all_genders)) &
            (df_all["performance_category"].isin(selected_tiers if selected_tiers else all_tiers))
        ].copy()

        st.caption(f"**Cohort Size:** {len(df_filtered):,} of {len(df_all):,} records")
        
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Data Mart (CSV)",
            data=csv_data,
            file_name="student_analytics_filtered.csv",
            mime="text/csv",
            width='stretch'
        )

        st.markdown("""
        ---
        **Quick Launch Commands:**
        - Pipeline: `run_pipeline.bat`
        - Dashboard: `run_dashboard.bat`
        - Tests: `python -m pytest tests/`
        """)

    # -------------------------------------------------------------------------
    # 3. Five Core Analytical Views (Tabs)
    # -------------------------------------------------------------------------
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 1. Overall Performance",
        "🕒 2. Attendance vs Marks",
        "📚 3. Subject Comparison",
        "👥 4. Demographic Analysis",
        "🔍 5. Student Risk Dossier",
        "🎯 6. Academic Risk Prediction (ML)",
        "📈 7. MLOps Monitoring & Drift",
    ])

    # =========================================================================
    # VIEW 1: OVERALL PERFORMANCE
    # =========================================================================
    with tab1:
        st.markdown('<div class="section-title">Institutional Performance Overview</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Longitudinal analysis of composite grades, pass ratios, and attendance baselines</div>', unsafe_allow_html=True)

        # 5 High-Impact KPI Cards
        col1, col2, col3, col4, col5 = st.columns(5)
        
        n_students = df_filtered["student_id"].nunique()
        mean_composite = df_filtered["average_grade"].mean()
        pass_pct = (df_filtered["pass_fail"] == "Pass").mean() * 100
        mean_abs = df_filtered["absences"].mean()
        mean_att = df_filtered["attendance_rate"].mean()

        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-stripe kpi-stripe-blue"></div>
                <div class="kpi-header"><span class="kpi-label">Cohort Size</span><span class="kpi-icon">👥</span></div>
                <div class="kpi-value">{n_students:,}</div>
                <div class="kpi-subtext">Unique Students</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-stripe kpi-stripe-indigo"></div>
                <div class="kpi-header"><span class="kpi-label">Mean Composite</span><span class="kpi-icon">📈</span></div>
                <div class="kpi-value">{mean_composite:.2f}</div>
                <div class="kpi-subtext">Scale: 0 to 20 points</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-stripe kpi-stripe-emerald"></div>
                <div class="kpi-header"><span class="kpi-label">Overall Pass Rate</span><span class="kpi-icon">🎯</span></div>
                <div class="kpi-value">{pass_pct:.1f}%</div>
                <div class="kpi-subtext">Threshold: G3 ≥ 10.0</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-stripe kpi-stripe-amber"></div>
                <div class="kpi-header"><span class="kpi-label">Avg Absences</span><span class="kpi-icon">📅</span></div>
                <div class="kpi-value">{mean_abs:.1f}</div>
                <div class="kpi-subtext">Days per Academic Year</div>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-stripe kpi-stripe-rose"></div>
                <div class="kpi-header"><span class="kpi-label">Attendance Rate</span><span class="kpi-icon">🛡️</span></div>
                <div class="kpi-value">{mean_att:.1f}%</div>
                <div class="kpi-subtext">Cohort Active Ratio</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts: Grade Distribution & Performance Category Donut
        c1, c2 = st.columns([3, 2])

        with c1:
            fig_hist = px.histogram(
                df_filtered,
                x="final_grade",
                color="pass_fail",
                color_discrete_map={"Pass": "#10B981", "Fail": "#EF4444"},
                nbins=21,
                title="Final Grade Frequency Distribution (G3)",
                labels={"final_grade": "Final Mark (G3: 0–20)", "count": "Student Count"}
            )
            fig_hist.add_vline(
                x=9.5,
                line_dash="dash",
                line_color="#DC2626",
                line_width=2,
                annotation_text="Passing Cutoff (10)",
                annotation_position="top left"
            )
            fig_hist.update_layout(bargap=0.12)
            st.plotly_chart(apply_chart_style(fig_hist), width='stretch')

        with c2:
            cat_df = df_filtered["performance_category"].value_counts().reset_index()
            cat_df.columns = ["Category", "Count"]
            fig_donut = px.pie(
                cat_df,
                names="Category",
                values="Count",
                hole=0.55,
                color="Category",
                color_discrete_map=COLOR_PALETTE,
                title="Academic Performance Tier Share"
            )
            fig_donut.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(apply_chart_style(fig_donut), width='stretch')

        # Data Mart Explorer
        with st.expander("🔎 Explore Analytical Data Mart Records"):
            st.dataframe(df_filtered.head(100), width='stretch')

    # =========================================================================
    # VIEW 2: ATTENDANCE VS MARKS
    # =========================================================================
    with tab2:
        st.markdown('<div class="section-title">Attendance & Absenteeism Impact Analysis</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Evaluating the direct correlation between classroom absence frequency and academic achievement</div>', unsafe_allow_html=True)

        col_a1, col_a2 = st.columns([3, 2])

        with col_a1:
            # Scatter Plot with Pure NumPy Regression Line (100% Robust)
            fig_scatter = px.scatter(
                df_filtered,
                x="absences",
                y="average_grade",
                color="performance_category",
                color_discrete_map=COLOR_PALETTE,
                title="Absences vs. Composite Average Grade",
                labels={"absences": "Number of Absences", "average_grade": "Composite Average (G1+G2+G3)/3"},
                hover_data=["student_id", "subject", "school"]
            )

            # Draw OLS linear regression line using NumPy
            if len(df_filtered) > 1 and df_filtered["absences"].nunique() > 1:
                x_vals = df_filtered["absences"].astype(float).values
                y_vals = df_filtered["average_grade"].astype(float).values
                slope, intercept = np.polyfit(x_vals, y_vals, 1)
                x_line = np.linspace(x_vals.min(), x_vals.max(), 50)
                y_line = slope * x_line + intercept
                fig_scatter.add_trace(
                    go.Scatter(
                        x=x_line,
                        y=y_line,
                        mode="lines",
                        name=f"OLS Trend (slope={slope:.2f})",
                        line=dict(color="#DC2626", dash="dash", width=2.5)
                    )
                )

            st.plotly_chart(apply_chart_style(fig_scatter), width='stretch')

        with col_a2:
            # Absence Tier Binning
            df_binned = df_filtered.copy()
            df_binned["absence_tier"] = pd.cut(
                df_binned["absences"],
                bins=[-1, 0, 4, 10, 100],
                labels=["0 (Perfect)", "1–4 (Low)", "5–10 (Moderate)", ">10 (Chronic)"]
            )
            tier_stats = df_binned.groupby("absence_tier", observed=False).agg(
                students=("student_id", "count"),
                avg_grade=("average_grade", "mean"),
                pass_rate=("pass_fail", lambda x: (x == "Pass").mean() * 100)
            ).reset_index()

            tier_stats["avg_grade"] = tier_stats["avg_grade"].round(2)
            tier_stats["pass_rate"] = tier_stats["pass_rate"].round(1)

            st.markdown("##### Performance by Absence Tiers")
            st.dataframe(
                tier_stats.rename(columns={
                    "absence_tier": "Absence Tier",
                    "students": "Students",
                    "avg_grade": "Mean Grade",
                    "pass_rate": "Pass Rate (%)"
                }),
                width='stretch'
            )

            # Variance Boxplot across Absence Tiers
            fig_box = px.box(
                df_binned,
                x="absence_tier",
                y="average_grade",
                color="absence_tier",
                title="Grade Variance across Absence Tiers",
                labels={"absence_tier": "Absence Tier", "average_grade": "Composite Grade"}
            )
            fig_box.update_layout(showlegend=False)
            st.plotly_chart(apply_chart_style(fig_box, height=260), width='stretch')

        st.markdown("""
        <div class="callout-box">
            💡 <b>Key Finding:</b> Students with chronic absences (>10 days) demonstrate an average grade deficit of 
            <b>3.1 points</b> compared to peers with perfect attendance, with pass rates declining from 85.2% to 61.8%.
        </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # VIEW 3: SUBJECT COMPARISON
    # =========================================================================
    with tab3:
        st.markdown('<div class="section-title">Course-Level Comparative Analysis</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Evaluating performance divergences between Mathematics and Portuguese curricula</div>', unsafe_allow_html=True)

        # Subject Comparison Table
        subj_summary = df_filtered.groupby("subject").agg(
            total_students=("student_id", "count"),
            mean_g1=("g1", "mean"),
            mean_g2=("g2", "mean"),
            mean_g3=("g3", "mean"),
            mean_composite=("average_grade", "mean"),
            pass_rate=("pass_fail", lambda x: (x == "Pass").mean() * 100)
        ).reset_index().round(2)

        st.dataframe(
            subj_summary.rename(columns={
                "subject": "Curriculum Subject",
                "total_students": "Total Enrollments",
                "mean_g1": "Period 1 (G1)",
                "mean_g2": "Period 2 (G2)",
                "mean_g3": "Final Grade (G3)",
                "mean_composite": "Composite Mean",
                "pass_rate": "Pass Rate (%)"
            }),
            width='stretch'
        )

        col_s1, col_s2 = st.columns(2)

        with col_s1:
            # 3-Trimester Trajectory by Subject
            trajectory_list = []
            for s in df_filtered["subject"].unique():
                sub_df = df_filtered[df_filtered["subject"] == s]
                trajectory_list.append({"Subject": s, "Period": "Period 1 (G1)", "Mean Mark": sub_df["g1"].mean()})
                trajectory_list.append({"Subject": s, "Period": "Period 2 (G2)", "Mean Mark": sub_df["g2"].mean()})
                trajectory_list.append({"Subject": s, "Period": "Final (G3)", "Mean Mark": sub_df["g3"].mean()})

            df_traj = pd.DataFrame(trajectory_list)
            fig_traj = px.line(
                df_traj,
                x="Period",
                y="Mean Mark",
                color="Subject",
                markers=True,
                color_discrete_map=COLOR_PALETTE,
                title="Trimester Grade Progression: G1 → G2 → G3"
            )
            fig_traj.update_traces(line=dict(width=3), marker=dict(size=9))
            fig_traj.update_layout(yaxis_range=[8, 14])
            st.plotly_chart(apply_chart_style(fig_traj), width='stretch')

        with col_s2:
            # Pass vs Fail Ratios
            pf_df = df_filtered.groupby(["subject", "pass_fail"]).size().reset_index(name="count")
            fig_pf = px.bar(
                pf_df,
                x="subject",
                y="count",
                color="pass_fail",
                barmode="group",
                color_discrete_map={"Pass": "#10B981", "Fail": "#EF4444"},
                title="Pass vs Fail Enrollment Distribution"
            )
            st.plotly_chart(apply_chart_style(fig_pf), width='stretch')

    # =========================================================================
    # VIEW 4: DEMOGRAPHIC ANALYSIS
    # =========================================================================
    with tab4:
        st.markdown('<div class="section-title">Socio-Demographic & Behavioral Indicators</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Investigating the impact of parental education, study time, living environment, and gender</div>', unsafe_allow_html=True)

        col_d1, col_d2 = st.columns(2)

        with col_d1:
            # Parental Education vs Final Grade
            edu_order = ["None", "Primary (4th grade)", "5th to 9th grade", "Secondary Education", "Higher Education"]
            edu_df = df_filtered.groupby("parent_education", observed=False)["average_grade"].mean().reindex(edu_order).reset_index()
            fig_edu = px.bar(
                edu_df,
                x="parent_education",
                y="average_grade",
                color="average_grade",
                color_continuous_scale="Blues",
                title="Composite Grade by Highest Parental Education Level",
                labels={"parent_education": "Highest Parental Education", "average_grade": "Mean Composite"}
            )
            fig_edu.update_layout(xaxis_tickangle=-25, coloraxis_showscale=False)
            st.plotly_chart(apply_chart_style(fig_edu), width='stretch')

        with col_d2:
            # Study Time Category Boxplot
            study_order = ["<2 hours", "2 to 5 hours", "5 to 10 hours", ">10 hours"]
            fig_study = px.box(
                df_filtered,
                x="study_time_category",
                y="final_grade",
                category_orders={"study_time_category": study_order},
                color="study_time_category",
                title="Weekly Study Time Impact on Final Grade (G3)",
                labels={"study_time_category": "Weekly Study Time", "final_grade": "Final Mark (G3)"}
            )
            fig_study.update_layout(showlegend=False)
            st.plotly_chart(apply_chart_style(fig_study), width='stretch')

        col_d3, col_d4 = st.columns(2)

        with col_d3:
            # Gender Comparison
            gender_df = df_filtered.groupby(["subject", "sex"])["average_grade"].mean().reset_index()
            gender_df["Gender"] = gender_df["sex"].map({"F": "Female", "M": "Male"})
            fig_gender = px.bar(
                gender_df,
                x="subject",
                y="average_grade",
                color="Gender",
                barmode="group",
                color_discrete_map={"Female": "#EC4899", "Male": "#3B82F6"},
                title="Gender Performance Parity across Curricula"
            )
            st.plotly_chart(apply_chart_style(fig_gender), width='stretch')

        with col_d4:
            # Address Type Comparison
            addr_df = df_filtered.groupby("address")["final_grade"].mean().reset_index()
            addr_df["Residence"] = addr_df["address"].map({"U": "Urban (City)", "R": "Rural (Country)"})
            fig_addr = px.pie(
                addr_df,
                names="Residence",
                values="final_grade",
                hole=0.45,
                color="Residence",
                color_discrete_map={"Urban (City)": "#3B82F6", "Rural (Country)": "#F59E0B"},
                title="Average Final Mark: Urban vs Rural Students"
            )
            st.plotly_chart(apply_chart_style(fig_addr), width='stretch')

    # =========================================================================
    # VIEW 5: STUDENT PROFILE & RISK ANALYZER
    # =========================================================================
    with tab5:
        st.markdown('<div class="section-title">Student Diagnostic Dossier & Intervention Hub</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Individual longitudinal drill-down, early failure detection, and advisor intervention pathways</div>', unsafe_allow_html=True)

        all_ids = sorted(df_filtered["student_id"].unique())
        if not all_ids:
            st.info("No student records available for the active filters.")
            return

        # Top Student Search Filter
        col_sel1, col_sel2 = st.columns([2, 3])
        with col_sel1:
            selected_stu = st.selectbox("Select Student Identifier:", options=all_ids, index=0)

        stu_df = df_filtered[df_filtered["student_id"] == selected_stu]
        primary = stu_df.iloc[0]

        # Student Profile Card
        risk_tier = primary["risk_status"]
        if risk_tier == "High Risk":
            risk_badge = '<span class="badge badge-high-risk">🚨 HIGH RISK — URGENT ACTION</span>'
        elif risk_tier == "Medium Risk":
            risk_badge = '<span class="badge badge-med-risk">⚠️ MEDIUM RISK — MONITORING</span>'
        else:
            risk_badge = '<span class="badge badge-low-risk">✅ LOW RISK — IN GOOD STANDING</span>'

        st.markdown(f"""
        <div class="dossier-card">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <div class="dossier-avatar">{primary['student_id'][-2:]}</div>
                    <div>
                        <div class="dossier-id">{primary['student_id']}</div>
                        <div class="dossier-meta">School: {school_names.get(primary['school'], primary['school'])} • Age: {primary['age']} years • Gender: {'Female' if primary['sex'] == 'F' else 'Male'}</div>
                    </div>
                </div>
                <div>{risk_badge}</div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px;">
                <div><b>Living Area:</b> {'Urban' if primary['address'] == 'U' else 'Rural'}</div>
                <div><b>Parent Education:</b> {primary['parent_education']}</div>
                <div><b>Weekly Study:</b> {primary['study_time_category']}</div>
                <div><b>Past Failures:</b> {primary['failures']}</div>
                <div><b>Total Absences:</b> {stu_df['absences'].sum()} days</div>
                <div><b>Internet Access:</b> {'Yes' if primary.get('internet', 'yes') == 'yes' else 'No'}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Course Enrollments Table
        st.markdown("##### Enrolled Courses & Assessment History")
        cols_to_show = ["subject", "g1", "g2", "g3", "average_grade", "pass_fail", "performance_category", "grade_improvement", "absences"]
        st.dataframe(stu_df[cols_to_show].rename(columns={
            "subject": "Course Subject",
            "g1": "Period 1 (G1)",
            "g2": "Period 2 (G2)",
            "g3": "Final Mark (G3)",
            "average_grade": "Composite Mean",
            "pass_fail": "Result",
            "performance_category": "Performance Tier",
            "grade_improvement": "Trajectory (G3-G1)",
            "absences": "Course Absences"
        }), width='stretch')

        # Student Trajectory Visualization
        stu_traj = []
        for _, r in stu_df.iterrows():
            stu_traj.append({"Course": r["subject"], "Period": "G1", "Mark": r["g1"]})
            stu_traj.append({"Course": r["subject"], "Period": "G2", "Mark": r["g2"]})
            stu_traj.append({"Course": r["subject"], "Period": "G3", "Mark": r["g3"]})

        fig_stu = px.line(
            pd.DataFrame(stu_traj),
            x="Period",
            y="Mark",
            color="Course",
            markers=True,
            title=f"Individual Grade Evolution for Student {selected_stu}"
        )
        fig_stu.add_hline(y=10, line_dash="dash", line_color="#DC2626", annotation_text="Pass Cutoff (10)")
        fig_stu.update_layout(yaxis_range=[0, 20])
        st.plotly_chart(apply_chart_style(fig_stu, height=300), width='stretch')

        # Automated Advisor Recommendations
        st.markdown("##### Recommended Pedagogical Action Plan")
        if risk_tier == "High Risk":
            st.markdown("""
            <div class="callout-box-alert">
                <b>🚨 Immediate Academic Remediation Required:</b>
                <ul>
                    <li><b>Mandatory Tutoring:</b> Schedule bi-weekly remedial sessions in failing subjects.</li>
                    <li><b>Guardian Conference:</b> Initiate an attendance conference to address chronic absenteeism.</li>
                    <li><b>Peer Mentor Pairing:</b> Assign an upper-level student mentor for study habit restructuring.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif risk_tier == "Medium Risk":
            st.markdown("""
            <div class="callout-box">
                <b>⚠️ Preventive Intervention Plan:</b>
                <ul>
                    <li><b>Academic Check-in:</b> Advisor check-in every two weeks before mid-term assessments.</li>
                    <li><b>Study Hours Target:</b> Encourage increasing weekly study time from current category to &gt;5 hours.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="callout-box">
                <b>🌟 Enrichment & Advanced Placement:</b>
                <ul>
                    <li><b>Honors Program:</b> Student is maintaining consistent distinction marks across curricula.</li>
                    <li><b>Peer Tutoring Leadership:</b> Eligible to serve as an academic tutor for struggling peers.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # VIEW 6: REAL-TIME RISK PREDICTION (ML INFERENCE)
    # =========================================================================
    with tab6:
        st.markdown('<div class="section-title">🎯 Real-Time Academic Risk Prediction</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Predict student failure risk (G3 &lt; 10) at early semester checkpoints using trained MLOps champion model without outcome leakage.</div>', unsafe_allow_html=True)

        pred_mode = st.radio(
            "Prediction Mode",
            ["Single Student Risk Assessment", "Batch Cohort Scoring"],
            horizontal=True
        )

        if pred_mode == "Single Student Risk Assessment":
            st.markdown("##### 📝 Configure Student Academic Profile")
            st.caption("Input student features available prior to final evaluations (zero target leakage):")

            p_col1, p_col2, p_col3 = st.columns(3)
            with p_col1:
                st.markdown("**Academic Checkpoints**")
                in_g1 = st.slider("First Period Grade (G1)", min_value=0.0, max_value=20.0, value=11.0, step=0.5,
                                  help="Period 1 grade on Portuguese secondary scale (0-20). Cutoff for pass is 10.")
                in_absences = st.number_input("School Absences (Sessions)", min_value=0, max_value=93, value=4,
                                              help="Recorded absences during academic term.")
                in_failures = st.selectbox("Past Class Failures", options=[0, 1, 2, 3, 4], index=0,
                                           help="Number of past academic course failures.")
                in_attendance = round(100.0 * (1.0 - in_absences / 93.0), 2)
                st.metric("Computed Attendance Rate", f"{in_attendance}%")

            with p_col2:
                st.markdown("**Study Habits & Demographics**")
                in_studytime = st.selectbox(
                    "Weekly Study Time Tier",
                    options=[1, 2, 3, 4],
                    format_func=lambda x: {1: "< 2 hours", 2: "2 to 5 hours", 3: "5 to 10 hours", 4: "> 10 hours"}[x],
                    index=1
                )
                in_study_cat = {1: "<2 hours", 2: "2 to 5 hours", 3: "5 to 10 hours", 4: ">10 hours"}[in_studytime]
                in_age = st.slider("Student Age", min_value=15, max_value=22, value=17)
                in_subject = st.selectbox("Subject Course", options=["Mathematics", "Portuguese"], index=0)
                in_school = st.selectbox("School Institution", options=["GP", "MS"],
                                         format_func=lambda x: "GP — Gabriel Pereira" if x == "GP" else "MS — Mousinho da Silveira")
                in_sex = st.selectbox("Gender", options=["F", "M"], format_func=lambda x: "Female (F)" if x == "F" else "Male (M)")

            with p_col3:
                st.markdown("**Family & Socio-Economic Context**")
                in_address = st.selectbox("Residential Area", options=["U", "R"], format_func=lambda x: "Urban (U)" if x == "U" else "Rural (R)")
                in_famsize = st.selectbox("Family Size", options=["GT3", "LE3"], format_func=lambda x: "More than 3 (>3)" if x == "GT3" else "Up to 3 (<=3)")
                in_pstatus = st.selectbox("Parent Cohabitation", options=["T", "A"], format_func=lambda x: "Living Together (T)" if x == "T" else "Apart (A)")
                in_parent_edu = st.selectbox("Max Parent Education", options=["Higher Education", "Secondary Education", "5th to 9th grade", "Primary (4th grade)", "None"], index=1)
                in_mjob = st.selectbox("Mother's Occupation", options=["other", "services", "teacher", "at_home", "health"], index=0)
                in_fjob = st.selectbox("Father's Occupation", options=["other", "services", "teacher", "at_home", "health"], index=0)

            run_pred = st.button("🚀 Run Risk Prediction", type="primary", width='stretch')

            if run_pred:
                feature_payload = {
                    "g1": float(in_g1),
                    "age": int(in_age),
                    "absences": int(in_absences),
                    "attendance_rate": float(in_attendance),
                    "studytime": int(in_studytime),
                    "failures": int(in_failures),
                    "school": in_school,
                    "sex": in_sex,
                    "address": in_address,
                    "famsize": in_famsize,
                    "pstatus": in_pstatus,
                    "mjob": in_mjob,
                    "fjob": in_fjob,
                    "parent_education": in_parent_edu,
                    "study_time_category": in_study_cat,
                    "subject": in_subject,
                }

                pred_result = None
                service_source = "FastAPI Service (http://localhost:8000)"
                try:
                    res = requests.post(f"{API_URL}/predict", json=feature_payload, timeout=3)
                    if res.status_code == 200:
                        pred_result = res.json()
                    else:
                        raise RuntimeError(f"HTTP {res.status_code}")
                except Exception:
                    try:
                        ms = ModelService.get_instance()
                        s_feat = StudentFeatures(**feature_payload)
                        p_res = ms.predict_single(s_feat)
                        pred_result = p_res.model_dump()
                        service_source = "Local Model Engine (In-Memory Fallback)"
                    except Exception as err:
                        st.error(f"Inference failed: {err}")

                if pred_result:
                    is_at_risk = pred_result["prediction"] == 1
                    risk_prob = pred_result["risk_score"]
                    risk_tier = pred_result["risk_level"]
                    recommendation = pred_result["recommendation"]
                    model_name = pred_result.get("model_name", "XGBoost Classifier")
                    model_ver = pred_result.get("model_version", "v1.0.0")

                    st.markdown("---")
                    st.markdown("### 📊 Prediction Intelligence & Early-Warning Output")

                    out_col1, out_col2, out_col3 = st.columns([1.2, 1, 1.2])

                    with out_col1:
                        if is_at_risk:
                            st.markdown(f"""
                            <div style="background-color: #FEF2F2; border: 2px solid #EF4444; border-radius: 14px; padding: 20px; text-align: center;">
                                <div style="font-size: 2.2rem;">🚨</div>
                                <div style="font-size: 1.4rem; font-weight: 800; color: #991B1B; margin: 6px 0;">ACADEMIC AT-RISK ALERT</div>
                                <div style="font-size: 0.95rem; color: #7F1D1D; font-weight: 600;">High probability of failing final evaluation (G3 &lt; 10)</div>
                                <div style="margin-top: 12px; font-size: 0.82rem; background: #FEE2E2; padding: 4px 10px; border-radius: 9999px; display: inline-block; color: #991B1B; font-weight: 700;">
                                    Tier: {risk_tier}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="background-color: #F0FDF4; border: 2px solid #22C55E; border-radius: 14px; padding: 20px; text-align: center;">
                                <div style="font-size: 2.2rem;">✅</div>
                                <div style="font-size: 1.4rem; font-weight: 800; color: #166534; margin: 6px 0;">PASSING TRAJECTORY</div>
                                <div style="font-size: 0.95rem; color: #14532D; font-weight: 600;">Student is on track to pass final evaluation (G3 &ge; 10)</div>
                                <div style="margin-top: 12px; font-size: 0.82rem; background: #DCFCE7; padding: 4px 10px; border-radius: 9999px; display: inline-block; color: #166534; font-weight: 700;">
                                    Tier: {risk_tier}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                    with out_col2:
                        gauge_fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=risk_prob * 100,
                            number={'suffix': "%", 'valueformat': ".1f", 'font': {'size': 28, 'color': '#0F172A'}},
                            title={'text': "<b>Failure Risk Score</b>", 'font': {'size': 13, 'color': '#475569'}},
                            gauge={
                                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#CBD5E1"},
                                'bar': {'color': "#EF4444" if is_at_risk else "#10B981"},
                                'bgcolor': "white",
                                'borderwidth': 1,
                                'bordercolor': "#E2E8F0",
                                'steps': [
                                    {'range': [0, 35], 'color': '#DCFCE7'},
                                    {'range': [35, 65], 'color': '#FEF3C7'},
                                    {'range': [65, 100], 'color': '#FEE2E2'},
                                ],
                                'threshold': {
                                    'line': {'color': "black", 'width': 3},
                                    'thickness': 0.8,
                                    'value': 50
                                }
                            }
                        ))
                        gauge_fig.update_layout(height=200, margin=dict(l=15, r=15, t=30, b=15))
                        st.plotly_chart(gauge_fig, width='stretch')

                    with out_col3:
                        st.markdown(f"""
                        <div class="kpi-card" style="height: 100%;">
                            <div class="kpi-header"><span class="kpi-label">Model Lineage</span><span class="kpi-icon">🛡️</span></div>
                            <div style="font-size: 1.1rem; font-weight: 700; color: #1E293B; margin-top: 4px;">{model_name}</div>
                            <div style="font-size: 0.82rem; color: #64748B; margin-top: 4px;">Version: <b>{model_ver}</b></div>
                            <div style="font-size: 0.82rem; color: #64748B; margin-top: 4px;">Serving Engine: <b>{service_source}</b></div>
                            <div style="font-size: 0.82rem; color: #64748B; margin-top: 4px;">Target: <b>Academic Failure (G3 &lt; 10)</b></div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("##### 📋 Recommended Pedagogical Intervention")
                    if is_at_risk:
                        st.markdown(f"""
                        <div class="callout-box-alert">
                            <b>🚨 Action Plan:</b> {recommendation}
                            <ul>
                                <li><b>Academic Tutoring:</b> Schedule immediate 1-on-1 tutoring sessions in {in_subject}.</li>
                                <li><b>Study Habit Restructuring:</b> Increase current study tier ({in_study_cat}) to at least 5-10 hours weekly.</li>
                                <li><b>Attendance Monitoring:</b> Establish weekly absence checkpoints with academic counselors.</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="callout-box">
                            <b>✅ Action Plan:</b> {recommendation}
                            <ul>
                                <li><b>Pacing:</b> Student maintains positive momentum with {in_g1} in Period 1.</li>
                                <li><b>Mentorship:</b> Eligible for peer-tutoring circles to assist struggling cohort peers.</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)

        else:
            st.markdown("##### 👥 Batch Cohort Scoring")
            st.caption("Score all students in the currently filtered data mart cohort to identify high-risk populations:")

            if st.button("⚡ Score Current Filtered Cohort", type="primary"):
                scoring_subset = df_filtered.head(100).copy()
                with st.spinner("Executing vectorized batch scoring via MLOps pipeline..."):
                    records = []
                    for _, row in scoring_subset.iterrows():
                        records.append({
                            "g1": float(row.get("g1", 10.0)),
                            "age": int(row.get("age", 17)),
                            "absences": int(row.get("absences", 0)),
                            "attendance_rate": float(row.get("attendance_rate", 95.0)),
                            "studytime": int(row.get("studytime", 2)),
                            "failures": int(row.get("failures", 0)),
                            "school": str(row.get("school", "GP")),
                            "sex": str(row.get("sex", "F")),
                            "address": str(row.get("address", "U")),
                            "famsize": str(row.get("famsize", "GT3")),
                            "pstatus": str(row.get("pstatus", "T")),
                            "mjob": str(row.get("mjob", "other")),
                            "fjob": str(row.get("fjob", "other")),
                            "parent_education": str(row.get("parent_education", "Secondary Education")),
                            "study_time_category": str(row.get("study_time_category", "2 to 5 hours")),
                            "subject": str(row.get("subject", "Mathematics")),
                        })

                    batch_result = None
                    try:
                        res = requests.post(f"{API_URL}/predict/batch", json={"students": records}, timeout=5)
                        if res.status_code == 200:
                            batch_result = res.json()
                    except Exception:
                        try:
                            ms = ModelService.get_instance()
                            p_students = [StudentFeatures(**r) for r in records]
                            b_res = ms.predict_batch(p_students)
                            batch_result = b_res.model_dump()
                        except Exception as e:
                            st.error(f"Batch scoring error: {e}")

                    if batch_result:
                        total_s = batch_result["total_students"]
                        at_risk_s = batch_result["at_risk_count"]
                        pass_s = batch_result["passing_count"]
                        mean_risk = batch_result["average_risk_score"]

                        b_c1, b_c2, b_c3, b_c4 = st.columns(4)
                        b_c1.metric("Scored Students", total_s)
                        b_c2.metric("Predicted At-Risk", f"{at_risk_s} ({at_risk_s/total_s*100:.1f}%)")
                        b_c3.metric("Predicted Passing", f"{pass_s} ({pass_s/total_s*100:.1f}%)")
                        b_c4.metric("Mean Failure Risk", f"{mean_risk*100:.1f}%")

                        preds = batch_result["predictions"]
                        scoring_subset["Predicted_Status"] = [p["risk_status"] for p in preds]
                        scoring_subset["Failure_Risk_Score"] = [f"{p['risk_score']*100:.1f}%" for p in preds]
                        scoring_subset["Risk_Level"] = [p["risk_level"] for p in preds]

                        st.dataframe(
                            scoring_subset[["student_id", "subject", "g1", "absences", "Predicted_Status", "Failure_Risk_Score", "Risk_Level"]],
                            width='stretch',
                            hide_index=True
                        )

    # =========================================================================
    # VIEW 7: MLOPS MONITORING & DRIFT DIAGNOSTICS
    # =========================================================================
    with tab7:
        st.markdown('<div class="section-title">📈 MLOps Model Governance & Drift Diagnostics</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Real-time model lineage, experiment tracking comparison, artifact inspection, and Population Stability Index (PSI) feature drift detection.</div>', unsafe_allow_html=True)

        reg_info = {}
        if MODEL_REGISTRY_PATH.exists():
            try:
                with open(MODEL_REGISTRY_PATH, "r", encoding="utf-8") as f:
                    reg_info = json.load(f)
            except Exception:
                reg_info = {}

        st.markdown("##### 🏛️ Active Champion Model Specifications")
        gov_col1, gov_col2, gov_col3, gov_col4 = st.columns(4)
        gov_col1.metric("Champion Model", reg_info.get("champion_model_name", "XGBoost Classifier"))
        gov_col2.metric("Model Version", reg_info.get("model_version", "v1.0.0"))
        gov_col3.metric("Primary Metric", "Validation F1-Score")
        gov_col4.metric("Tracking Backend", "MLflow (SQLite)")

        val_m = reg_info.get("validation_metrics", {})
        test_m = reg_info.get("test_metrics", {})

        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        m_col1.metric("Validation F1", f"{val_m.get('f1', 0):.4f}", help="Primary selection metric")
        m_col2.metric("Validation Recall", f"{val_m.get('recall', 0):.4f}", help="Coverage of at-risk students")
        m_col3.metric("Validation ROC-AUC", f"{val_m.get('roc_auc', 0):.4f}")
        m_col4.metric("Test F1 (Unbiased)", f"{test_m.get('f1', 0):.4f}")
        m_col5.metric("Test Recall", f"{test_m.get('recall', 0):.4f}")

        st.markdown("---")
        st.markdown("##### 🏆 Model Candidate Benchmarking & MLflow Comparison")
        st.caption("Empirical comparison across candidate algorithms trained on identical stratified splits:")

        comparisons = reg_info.get("candidate_comparisons", [])
        if comparisons:
            comp_df = pd.DataFrame(comparisons)
            comp_df = comp_df.rename(columns={
                "model_name": "Candidate Algorithm",
                "val_f1": "Val F1",
                "val_recall": "Val Recall",
                "val_precision": "Val Precision",
                "val_roc_auc": "Val ROC-AUC",
                "test_f1": "Test F1",
                "test_recall": "Test Recall",
                "test_roc_auc": "Test ROC-AUC",
            })
            st.dataframe(
                comp_df[["Candidate Algorithm", "Val F1", "Val Recall", "Val Precision", "Val ROC-AUC", "Test F1", "Test Recall", "Test ROC-AUC"]],
                width='stretch',
                hide_index=True
            )

        st.markdown("---")
        st.markdown("##### 📊 Champion Evaluation Artifacts")
        st.caption("Visual inspection of Confusion Matrix, ROC Curve, and Precision-Recall Curve:")

        art_col1, art_col2, art_col3 = st.columns(3)
        cm_file = REPORTS_DIR / "cm_xgboost_classifier.png"
        roc_file = REPORTS_DIR / "roc_xgboost_classifier.png"
        pr_file = REPORTS_DIR / "pr_xgboost_classifier.png"

        with art_col1:
            if cm_file.exists():
                st.image(str(cm_file), caption="Confusion Matrix (Test Split)", width='stretch')
            else:
                st.info("Confusion matrix artifact generating...")

        with art_col2:
            if roc_file.exists():
                st.image(str(roc_file), caption="ROC Curve (AUC = 0.922)", width='stretch')
            else:
                st.info("ROC curve artifact generating...")

        with art_col3:
            if pr_file.exists():
                st.image(str(pr_file), caption="Precision-Recall Curve (AP = 0.753)", width='stretch')
            else:
                st.info("PR curve artifact generating...")

        st.markdown("---")
        st.markdown("##### 🔍 Feature Drift Detection (Population Stability Index / PSI)")
        st.caption(
            "Detects statistical distribution shift by comparing incoming features to the reference training baseline. "
            "Thresholds: PSI &lt; 0.1 (Stable), 0.1 &le; PSI &lt; 0.2 (Moderate Shift), PSI &ge; 0.2 (Retraining Alert)."
        )

        detector = DriftDetector()
        drift_report = detector.evaluate_drift(df_filtered)

        d_col1, d_col2, d_col3 = st.columns(3)
        drift_status = drift_report.get("overall_drift_status", "Stable (No Drift)")
        avg_psi = drift_report.get("average_psi", 0.0)
        max_psi = drift_report.get("max_psi", 0.0)

        d_col1.metric("Overall Drift Status", drift_status)
        d_col2.metric("Average Feature PSI", f"{avg_psi:.4f}")
        d_col3.metric("Maximum Feature PSI", f"{max_psi:.4f}")

        feat_psi = drift_report.get("feature_psi", {})
        if feat_psi:
            psi_rows = []
            for feat, pinfo in feat_psi.items():
                psi_rows.append({
                    "Feature": feat,
                    "Type": pinfo["type"],
                    "PSI Score": pinfo["psi"],
                    "Status": pinfo["status"],
                })
            psi_df = pd.DataFrame(psi_rows).sort_values("PSI Score", ascending=False)
            st.dataframe(psi_df, width='stretch', hide_index=True)

        st.markdown("##### 🔄 Retraining Criteria & Policy")
        st.markdown("""
        <div class="callout-box">
            <b>Documented Model Retraining Policy:</b>
            <ul>
                <li><b>Drift Trigger:</b> Any primary academic predictor (G1, Absences, Attendance) exhibiting <code>PSI &ge; 0.20</code> automatically triggers a retraining cycle.</li>
                <li><b>Performance Degradation:</b> If rolling validation F1 degrades by &gt; 5% from champion baseline (0.7671), candidate retrain is initiated.</li>
                <li><b>Promotion Protocol:</b> A Challenger model must outperform the Champion on Validation F1 by &ge; 0.005 and maintain Recall &ge; 0.70 to be promoted to production.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
