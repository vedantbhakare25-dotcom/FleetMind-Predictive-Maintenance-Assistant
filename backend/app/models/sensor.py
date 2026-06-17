# Pydantic schemas for sensor reading endpoints

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class SensorReadingCreate(BaseModel):
    """
    Schema for POST /api/sensors/readings request body.
    These are the exact keys the simulation script and
    IoT devices must send.
    """
    machine_id          : UUID
    air_temperature     : float = Field(..., ge=270, le=350,
                                        description="Air temperature in Kelvin")
    process_temperature : float = Field(..., ge=270, le=400,
                                        description="Process temperature in Kelvin")
    rotational_speed    : float = Field(..., ge=0, le=5000,
                                        description="Rotational speed in RPM")
    torque              : float = Field(..., ge=0, le=200,
                                        description="Torque in Nm")
    tool_wear           : float = Field(..., ge=0, le=300,
                                        description="Tool wear in minutes")

    # Optional CMAPSS sensors (for RUL model — future use)
    sensor_2  : Optional[float] = None
    sensor_3  : Optional[float] = None
    sensor_4  : Optional[float] = None
    sensor_7  : Optional[float] = None
    sensor_8  : Optional[float] = None
    sensor_9  : Optional[float] = None
    sensor_11 : Optional[float] = None
    sensor_12 : Optional[float] = None
    sensor_13 : Optional[float] = None
    sensor_14 : Optional[float] = None
    sensor_15 : Optional[float] = None
    sensor_17 : Optional[float] = None
    sensor_20 : Optional[float] = None
    sensor_21 : Optional[float] = None
    cycle_number : Optional[int] = None


class SensorReadingResponse(BaseModel):
    """
    Schema for POST /api/sensors/readings response.
    Confirms the reading was stored.
    """
    id          : UUID
    machine_id  : UUID
    recorded_at : datetime
    received    : bool = True

    class Config:
        from_attributes = True


class SensorLatestResponse(BaseModel):
    """
    Schema for GET /api/sensors/{machine_id}/latest response.
    Returns the most recent sensor values for display on the dashboard.
    """
    machine_id          : UUID
    recorded_at         : datetime
    air_temperature     : Optional[float]
    process_temperature : Optional[float]
    rotational_speed    : Optional[float]
    torque              : Optional[float]
    tool_wear           : Optional[float]

    # Engineered features — calculated and returned for display
    temp_diff           : Optional[float]
    power               : Optional[float]

    class Config:
        from_attributes = True