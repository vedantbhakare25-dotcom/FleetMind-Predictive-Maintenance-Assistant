# Prediction endpoints

from fastapi import APIRouter, Depends, Request
from uuid import UUID
from app.core.dependencies import engineer_or_above
from app.services.prediction_service import PredictionService

router = APIRouter()


@router.post("/run/{machine_id}")
async def run_prediction(
    machine_id : UUID,
    request    : Request,
    user       : dict = Depends(engineer_or_above)
):
    """
    Runs the full FleetMind prediction pipeline for a machine.
    Returns health score, failure probability, SHAP explanation,
    RUL estimate, and root cause analysis.
    """
    plant_id = user.get("plant_id")

    if not plant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not assigned to a plant."
        )

    return await PredictionService.run_full_pipeline(
        machine_id = machine_id,
        plant_id   = plant_id,
        request    = request
    )


@router.get("/{machine_id}/latest")
async def get_latest_prediction(
    machine_id : UUID,
    user       : dict = Depends(engineer_or_above)
):
    """
    Returns the most recent prediction for a machine,
    reshaped into the same nested structure as POST /run/{machine_id}
    so the frontend can use one consistent shape everywhere.
    """
    from app.db.supabase_client import supabase

    response = supabase.table("predictions") \
        .select("*") \
        .eq("machine_id", str(machine_id)) \
        .order("predicted_at", desc=True) \
        .limit(1) \
        .execute()

    if not response.data:
        return {"message": "No predictions found for this machine"}

    row = response.data[0]

    # Reshape flat database row into the nested structure
    # the frontend expects (same shape as POST /run/{machine_id})
    return {
        "id"                  : row["id"],
        "machine_id"          : row["machine_id"],
        "predicted_at"        : row["predicted_at"],
        "failure_probability" : row["failure_probability"],
        "failure_predicted"   : row["failure_predicted"],
        "confidence"          : _prob_to_confidence(row["failure_probability"]),

        "health_score": {
            "score"             : row["health_score"],
            "level"             : row["alert_level"],
            "recommendation"    : _level_to_recommendation(row["alert_level"]),
            "failure_component" : None,
            "rul_component"     : None
        },

        "failure_modes": {
            "TWF"          : row.get("mode_twf_prob"),
            "HDF"          : row.get("mode_hdf_prob"),
            "PWF"          : row.get("mode_pwf_prob"),
            "OSF"          : row.get("mode_osf_prob"),
            "primary_mode" : row.get("primary_failure_mode"),
            "active_modes" : _active_modes(row)
        },

        "rul": {
            "cycles_remaining" : row.get("rul_cycles") or 0,
            "hours_remaining"  : row.get("rul_hours") or 0,
            "trend"            : _rul_trend(row["failure_probability"]),
            "rul_normalized"   : None
        },

        "explainability": {
            "baseline"             : 0.034,
            "prediction_from_shap" : row["failure_probability"],
            "top_factors"          : row.get("top_factors") or [],
            "risk_factors"         : [],
            "protective_factors"   : []
        },

        "root_cause": {
            "primary_cause"         : row.get("root_cause_text", "")[:80] if row.get("root_cause_text") else "No cause identified",
            "detailed_text"         : row.get("root_cause_text") or "",
            "active_modes"          : _active_modes(row),
            "contributing_features" : [f["feature"] for f in (row.get("top_factors") or [])],
            "confidence"            : "MEDIUM",
            "action_required"       : ""
        },

        "alert_created" : False,
        "alert_level"   : row["alert_level"],
        "model_version" : row.get("model_version", "1.0.0")
    }


def _prob_to_confidence(prob: float) -> str:
    if prob >= 0.90: return 'VERY HIGH'
    elif prob >= 0.75: return 'HIGH'
    elif prob >= 0.50: return 'MEDIUM'
    elif prob >= 0.30: return 'LOW'
    else: return 'VERY LOW'


def _level_to_recommendation(level: str) -> str:
    recs = {
        'CRITICAL': "IMMEDIATE ACTION REQUIRED — Stop machine and inspect.",
        'HIGH'    : "Schedule maintenance within 24 hours.",
        'MEDIUM'  : "Increase monitoring frequency.",
        'LOW'     : "Monitor closely. No immediate action required.",
        'NORMAL'  : "Machine operating within normal parameters."
    }
    return recs.get(level, "Monitor machine status.")


def _rul_trend(failure_prob: float) -> str:
    if failure_prob >= 0.75: return 'CRITICAL_DECLINE'
    elif failure_prob >= 0.50: return 'DECLINING'
    elif failure_prob >= 0.30: return 'GRADUAL_DECLINE'
    else: return 'STABLE'


def _active_modes(row: dict) -> list:
    modes = []
    if (row.get("mode_hdf_prob") or 0) >= 0.40: modes.append("HDF")
    if (row.get("mode_pwf_prob") or 0) >= 0.40: modes.append("PWF")
    if (row.get("mode_osf_prob") or 0) >= 0.40: modes.append("OSF")
    if (row.get("mode_twf_prob") or 0) >= 0.40: modes.append("TWF")
    return modes

@router.get("/{machine_id}/history")
async def get_prediction_history(
    machine_id : UUID,
    limit      : int = 20,
    user       : dict = Depends(engineer_or_above)
):
    """Returns prediction history for trend charts."""
    from app.db.supabase_client import supabase

    response = supabase.table("predictions") \
        .select(
            "id, predicted_at, failure_probability, "
            "health_score, alert_level, rul_cycles, primary_failure_mode"
        ) \
        .eq("machine_id", str(machine_id)) \
        .order("predicted_at", desc=True) \
        .limit(limit) \
        .execute()

    return response.data or []