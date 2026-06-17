# Machine management endpoints

from fastapi import APIRouter, Depends
from uuid import UUID
from app.core.dependencies import engineer_or_above
from app.services.machine_service import MachineService

router = APIRouter()


@router.get("")
async def get_machines(user: dict = Depends(engineer_or_above)):
    """
    Returns all machines for the user's plant with latest health data.
    Powers the main dashboard machine list.
    """
    plant_id = user.get("plant_id")
    if not plant_id:
        return {"machines": [], "summary": {}}

    machines = await MachineService.get_machines_for_plant(plant_id)
    summary  = await MachineService.get_plant_summary(plant_id)

    return {
        "machines" : machines,
        "summary"  : summary
    }


@router.get("/{machine_id}")
async def get_machine(
    machine_id : UUID,
    user       : dict = Depends(engineer_or_above)
):
    """Returns full details for one machine."""
    plant_id = user.get("plant_id")
    return await MachineService.get_machine(machine_id, plant_id)