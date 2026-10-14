"""
API Request and Response Schemas
--------------------------------
Pydantic data models for validating student features and structured prediction outputs.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone


class StudentFeatures(BaseModel):
    """Input features for student academic risk prediction (strictly leak-free)."""
    # Numerical Predictors
    g1: float = Field(..., ge=0.0, le=20.0, description="First period grade (0 to 20)", examples=[11.0])
    age: int = Field(..., ge=14, le=30, description="Student age in years", examples=[17])
    absences: int = Field(..., ge=0, le=100, description="Number of school absences", examples=[4])
    attendance_rate: float = Field(..., ge=0.0, le=100.0, description="Attendance percentage (0-100%)", examples=[95.7])
    studytime: int = Field(..., ge=1, le=4, description="Weekly study time tier (1: <2h, 2: 2-5h, 3: 5-10h, 4: >10h)", examples=[2])
    failures: int = Field(..., ge=0, le=5, description="Number of past class failures", examples=[0])

    # Categorical Predictors
    school: str = Field(default="GP", description="School ('GP' or 'MS')")
    sex: str = Field(default="F", description="Gender ('F' or 'M')")
    address: str = Field(default="U", description="Home address type ('U' for Urban, 'R' for Rural)")
    famsize: str = Field(default="GT3", description="Family size ('LE3' <= 3, 'GT3' > 3)")
    pstatus: str = Field(default="T", description="Parent cohabitation status ('T' Together, 'A' Apart)")
    mjob: str = Field(default="other", description="Mother job ('teacher', 'health', 'services', 'at_home', 'other')")
    fjob: str = Field(default="other", description="Father job ('teacher', 'health', 'services', 'at_home', 'other')")
    parent_education: str = Field(default="Secondary Education", description="Max parental education tier")
    study_time_category: str = Field(default="2 to 5 hours", description="Categorical study time bracket")
    subject: str = Field(default="Mathematics", description="Subject enrolled ('Mathematics' or 'Portuguese')")

    @field_validator("school")
    @classmethod
    def validate_school(cls, v: str) -> str:
        if v.upper() not in ["GP", "MS"]:
            raise ValueError("School must be 'GP' or 'MS'")
        return v.upper()

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: str) -> str:
        if v.upper() not in ["F", "M"]:
            raise ValueError("Sex must be 'F' or 'M'")
        return v.upper()

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        if v.upper() not in ["U", "R"]:
            raise ValueError("Address must be 'U' (urban) or 'R' (rural)")
        return v.upper()


class PredictionResponse(BaseModel):
    """Prediction outcome for a single student."""
    prediction: int = Field(..., description="0 = Passing, 1 = Academic Failure Risk")
    risk_status: str = Field(..., description="'Passing' or 'At-Risk'")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Estimated probability of academic failure")
    risk_level: str = Field(..., description="'Low Risk' (<0.35), 'Medium Risk' (0.35-0.65), 'High Risk' (>0.65)")
    recommendation: str = Field(..., description="Recommended academic intervention")
    model_name: str
    model_version: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BatchPredictionRequest(BaseModel):
    """Batch input payload containing multiple student records."""
    students: List[StudentFeatures]


class BatchPredictionResponse(BaseModel):
    """Aggregated batch prediction response."""
    total_students: int
    at_risk_count: int
    passing_count: int
    average_risk_score: float
    predictions: List[PredictionResponse]
    model_version: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HealthResponse(BaseModel):
    """API health status schema."""
    status: str
    model_loaded: bool
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ModelInfoResponse(BaseModel):
    """Model metadata and governance specification."""
    champion_model_name: str
    algorithm: str
    model_version: str
    target_definition: str
    selection_rationale: str
    validation_metrics: Dict[str, Any]
    test_metrics: Dict[str, Any]
    feature_columns: List[str]
    total_features: int
    timestamp: str
