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
    """Returns the most recent prediction for a machine."""
    from app.db.supabase_client import supabase

    response = supabase.table("predictions") \
        .select("*") \
        .eq("machine_id", str(machine_id)) \
        .order("predicted_at", desc=True) \
        .limit(1) \
        .execute()

    if not response.data:
        return {"message": "No predictions found for this machine"}

    return response.data[0]


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