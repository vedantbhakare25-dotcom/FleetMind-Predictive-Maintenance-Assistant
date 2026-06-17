# Pydantic schemas for prediction endpoints

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class SHAPFactor(BaseModel):
    """One SHAP feature contribution — used in the explainability panel."""
    feature    : str
    shap_value : float
    direction  : str    # 'RISK' or 'PROTECTIVE'
    percentage : float  # share of total SHAP impact


class FailureModesOutput(BaseModel):
    """Failure mode probabilities from the multi-label classifiers."""
    TWF          : float
    HDF          : float
    PWF          : float
    OSF          : float
    primary_mode : str
    active_modes : list[str]


class RULOutput(BaseModel):
    """Remaining Useful Life estimate."""
    cycles_remaining : int
    hours_remaining  : float
    trend            : str   # STABLE, DECLINING, CRITICAL_DECLINE
    rul_normalized   : float


class HealthScoreOutput(BaseModel):
    """Health score with level and trend."""
    score              : float
    level              : str    # NORMAL, LOW, MEDIUM, HIGH, CRITICAL
    recommendation     : str
    failure_component  : float
    rul_component      : float


class ExplainabilityOutput(BaseModel):
    """SHAP explanation for this prediction."""
    baseline             : float
    prediction_from_shap : float
    top_factors          : list[SHAPFactor]
    risk_factors         : list[dict]
    protective_factors   : list[dict]


class RootCauseOutput(BaseModel):
    """Root cause analysis result."""
    primary_cause         : str
    detailed_text         : str
    active_modes          : list[str]
    contributing_features : list[str]
    confidence            : str
    action_required       : str


class PredictionResponse(BaseModel):
    """
    Complete prediction response — returned by
    POST /api/predictions/run/{machine_id}

    This is the most important response schema in FleetMind.
    Everything the dashboard needs is in here.
    """
    id                  : UUID
    machine_id          : UUID
    predicted_at        : datetime

    # Core outputs
    failure_probability : float
    failure_predicted   : bool
    confidence          : str

    # All ML components
    health_score        : HealthScoreOutput
    failure_modes       : FailureModesOutput
    rul                 : RULOutput
    explainability      : ExplainabilityOutput
    root_cause          : RootCauseOutput

    # Alert info if one was created
    alert_created       : bool
    alert_level         : Optional[str]
    model_version       : str = "1.0.0"

    class Config:
        from_attributes = True


class PredictionSummary(BaseModel):
    """
    Lightweight prediction summary for machine list view.
    Doesn't include full SHAP details — just what the dashboard card needs.
    """
    machine_id          : UUID
    predicted_at        : datetime
    failure_probability : float
    health_score        : float
    alert_level         : str
    primary_failure_mode: Optional[str]
    rul_cycles          : Optional[int]