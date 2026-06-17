# Alert management endpoints

from fastapi import APIRouter, Depends
from uuid import UUID
from typing import Optional
from app.core.dependencies import engineer_or_above
from app.services.alert_service import AlertService

router = APIRouter()


@router.get("")
async def get_active_alerts(user: dict = Depends(engineer_or_above)):
    """Returns all active alerts for the plant."""
    plant_id = user.get("plant_id")
    if not plant_id:
        return []
    return await AlertService.get_active_alerts(plant_id)


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id : UUID,
    note     : Optional[str] = None,
    user     : dict = Depends(engineer_or_above)
):
    """Marks an alert as acknowledged."""
    return await AlertService.acknowledge_alert(
        alert_id = alert_id,
        user_id  = user["id"],
        note     = note
    )


@router.patch("/{alert_id}/resolve")
async def resolve_alert(
    alert_id        : UUID,
    resolution_note : Optional[str] = None,
    user            : dict = Depends(engineer_or_above)
):
    """Marks an alert as resolved."""
    return await AlertService.resolve_alert(
        alert_id        = alert_id,
        resolution_note = resolution_note
    )