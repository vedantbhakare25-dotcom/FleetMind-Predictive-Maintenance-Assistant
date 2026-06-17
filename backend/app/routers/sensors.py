# Sensor data ingestion endpoints

from fastapi import APIRouter, Depends, Request
from uuid import UUID
from app.core.dependencies import engineer_or_above
from app.models.sensor import SensorReadingCreate, SensorReadingResponse
from app.services.sensor_service import SensorService

router = APIRouter()


@router.post("/readings", response_model=SensorReadingResponse)
async def ingest_sensor_reading(
    reading : SensorReadingCreate,
    user    : dict = Depends(engineer_or_above)
):
    """
    Ingests a new sensor reading for a machine.
    Called by the simulation script or real IoT devices.
    """
    reading_dict = {
        "machine_id"          : str(reading.machine_id),
        "air_temperature"     : reading.air_temperature,
        "process_temperature" : reading.process_temperature,
        "rotational_speed"    : reading.rotational_speed,
        "torque"              : reading.torque,
        "tool_wear"           : reading.tool_wear,
        "sensor_2"            : reading.sensor_2,
        "sensor_3"            : reading.sensor_3,
        "sensor_4"            : reading.sensor_4,
        "sensor_7"            : reading.sensor_7,
        "sensor_8"            : reading.sensor_8,
        "sensor_9"            : reading.sensor_9,
        "sensor_11"           : reading.sensor_11,
        "sensor_12"           : reading.sensor_12,
        "sensor_13"           : reading.sensor_13,
        "sensor_14"           : reading.sensor_14,
        "sensor_15"           : reading.sensor_15,
        "sensor_17"           : reading.sensor_17,
        "sensor_20"           : reading.sensor_20,
        "sensor_21"           : reading.sensor_21,
        "cycle_number"        : reading.cycle_number
    }

    stored = await SensorService.insert_reading(reading_dict)
    return {**stored, "received": True}


@router.get("/{machine_id}/latest")
async def get_latest_sensor_reading(
    machine_id : UUID,
    user       : dict = Depends(engineer_or_above)
):
    """Returns the most recent sensor values for a machine."""
    reading = await SensorService.get_latest_reading(machine_id)

    if not reading:
        return {"message": "No sensor readings found for this machine"}

    # Add engineered features for display
    import numpy as np
    air  = reading.get("air_temperature", 0)
    proc = reading.get("process_temperature", 0)
    rpm  = reading.get("rotational_speed", 0)
    torq = reading.get("torque", 0)

    reading["temp_diff"] = round(proc - air, 2)
    reading["power"]     = round(torq * rpm * (2 * np.pi / 60), 2)

    return reading