# Pydantic schemas for machine endpoints

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class MachineResponse(BaseModel):
    """Full machine details."""
    id              : UUID
    plant_id        : UUID
    name            : str
    machine_type    : str
    model_number    : Optional[str]
    serial_number   : Optional[str]
    location        : Optional[str]
    status          : str
    quality_variant : str
    installed_at    : Optional[datetime]
    created_at      : datetime

    class Config:
        from_attributes = True


class MachineWithHealth(BaseModel):
    """
    Machine info combined with latest prediction summary.
    Used for the dashboard machine cards.
    """
    id              : UUID
    name            : str
    machine_type    : str
    location        : Optional[str]
    status          : str
    quality_variant : str

    # Latest health info — None if no predictions yet
    health_score        : Optional[float]
    alert_level         : Optional[str]
    failure_probability : Optional[float]
    rul_cycles          : Optional[int]
    last_predicted_at   : Optional[datetime]


class PlantSummary(BaseModel):
    """
    High-level summary of all machines in a plant.
    Powers the dashboard header cards.
    """
    total_machines  : int
    critical_count  : int
    high_count      : int
    medium_count    : int
    normal_count    : int
    offline_count   : int
    