# Business logic for sensor data operations

from uuid import UUID
from datetime import datetime
from app.db.supabase_client import supabase
from fastapi import HTTPException, status


class SensorService:

    @staticmethod
    async def insert_reading(reading_data: dict) -> dict:
        """
        Inserts one sensor reading into the sensor_readings table.

        Args:
            reading_data: dict matching sensor_readings table columns

        Returns:
            The inserted row with generated id and recorded_at
        """
        try:
            response = supabase.table("sensor_readings") \
                .insert(reading_data) \
                .execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to store sensor reading."
                )

            return response.data[0]

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error storing sensor reading: {str(e)}"
            )


    @staticmethod
    async def get_recent_readings(machine_id: UUID, limit: int = 30) -> list[dict]:
        """
        Fetches the most recent sensor readings for a machine.
        Used by prediction pipeline to get current sensor state.

        Args:
            machine_id: UUID of the machine
            limit: how many recent readings to fetch (default 30)

        Returns:
            List of reading dicts, ordered newest first
        """
        try:
            response = supabase.table("sensor_readings") \
                .select("*") \
                .eq("machine_id", str(machine_id)) \
                .order("recorded_at", desc=True) \
                .limit(limit) \
                .execute()

            return response.data or []

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error fetching sensor readings: {str(e)}"
            )


    @staticmethod
    async def get_latest_reading(machine_id: UUID) -> dict | None:
        """
        Fetches only the single most recent sensor reading.
        Used for the sensor display panel on the machine detail page.
        """
        readings = await SensorService.get_recent_readings(machine_id, limit=1)
        return readings[0] if readings else None