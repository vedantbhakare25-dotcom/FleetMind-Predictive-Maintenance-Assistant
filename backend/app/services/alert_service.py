# Business logic for alert lifecycle management

from uuid import UUID
from datetime import datetime
from app.db.supabase_client import supabase
from fastapi import HTTPException, status


ALERT_TITLES = {
    "CRITICAL" : "Critical failure risk detected",
    "HIGH"     : "High failure risk — maintenance required",
    "MEDIUM"   : "Elevated failure risk — monitor closely",
    "LOW"      : "Low-level anomaly detected"
}


class AlertService:

    @staticmethod
    async def create_alert(
        machine_id    : UUID,
        prediction_id : UUID,
        health_level  : str,
        failure_prob  : float,
        root_cause    : str,
        machine_name  : str = "Machine"
    ) -> dict | None:
        """
        Creates an alert record if the health level warrants one.
        Only creates alerts for MEDIUM, HIGH, and CRITICAL levels.

        Returns:
            The created alert dict, or None if no alert was needed
        """

        if health_level not in ("MEDIUM", "HIGH", "CRITICAL"):
            return None

        # Check if an active alert already exists for this machine
        # Avoid creating duplicate alerts for the same ongoing issue
        existing = supabase.table("alerts") \
            .select("id") \
            .eq("machine_id", str(machine_id)) \
            .eq("status", "active") \
            .eq("level", health_level) \
            .execute()

        if existing.data:
            # Active alert at same level already exists — don't duplicate
            return None

        alert_data = {
            "machine_id"    : str(machine_id),
            "prediction_id" : str(prediction_id),
            "level"         : health_level,
            "title"         : ALERT_TITLES.get(health_level, "Alert"),
            "message"       : (
                f"{machine_name} is showing {health_level.lower()} failure risk. "
                f"Failure probability: {failure_prob*100:.1f}%. "
                f"Immediate review recommended."
            ),
            "root_cause"    : root_cause,
            "status"        : "active"
        }

        try:
            response = supabase.table("alerts") \
                .insert(alert_data) \
                .execute()

            return response.data[0] if response.data else None

        except Exception as e:
            # Alert creation failure should not break prediction response
            print(f"Warning: Failed to create alert: {e}")
            return None


    @staticmethod
    async def get_active_alerts(plant_id: str) -> list[dict]:
        """
        Returns all active alerts for a plant, newest first.
        Used by the alert center and dashboard banner.
        """
        try:
            # Get machine IDs for this plant first
            machines = supabase.table("machines") \
                .select("id") \
                .eq("plant_id", plant_id) \
                .execute()

            if not machines.data:
                return []

            machine_ids = [m["id"] for m in machines.data]

            # Fetch active alerts for these machines
            response = supabase.table("alerts") \
                .select("*, machines(name, machine_type)") \
                .in_("machine_id", machine_ids) \
                .eq("status", "active") \
                .order("created_at", desc=True) \
                .execute()

            return response.data or []

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching alerts: {str(e)}"
            )


    @staticmethod
    async def acknowledge_alert(
        alert_id : UUID,
        user_id  : str,
        note     : str | None = None
    ) -> dict:
        """
        Marks an alert as acknowledged.
        Records who acknowledged it and when.
        """
        try:
            response = supabase.table("alerts") \
                .update({
                    "status"         : "acknowledged",
                    "acknowledged_by": user_id,
                    "acknowledged_at": datetime.utcnow().isoformat(),
                    "resolution_note": note
                }) \
                .eq("id", str(alert_id)) \
                .eq("status", "active") \
                .execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Alert not found or already acknowledged."
                )

            return response.data[0]

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error acknowledging alert: {str(e)}"
            )


    @staticmethod
    async def resolve_alert(
        alert_id        : UUID,
        resolution_note : str | None = None
    ) -> dict:
        """Marks an alert as resolved."""
        try:
            response = supabase.table("alerts") \
                .update({
                    "status"         : "resolved",
                    "resolved_at"    : datetime.utcnow().isoformat(),
                    "resolution_note": resolution_note
                }) \
                .eq("id", str(alert_id)) \
                .execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Alert not found."
                )

            return response.data[0]

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error resolving alert: {str(e)}"
            )