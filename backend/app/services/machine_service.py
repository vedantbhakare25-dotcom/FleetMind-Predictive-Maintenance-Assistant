# Business logic for machine data operations

from uuid import UUID
from app.db.supabase_client import supabase
from fastapi import HTTPException, status


class MachineService:

    @staticmethod
    async def get_machines_for_plant(plant_id: str) -> list[dict]:
        """
        Returns all machines belonging to a plant.
        Each machine is enriched with its latest prediction summary.
        """
        try:
            # Fetch all machines for this plant
            machines_response = supabase.table("machines") \
                .select("*") \
                .eq("plant_id", plant_id) \
                .neq("status", "decommissioned") \
                .order("name") \
                .execute()

            machines = machines_response.data or []

            # For each machine, fetch its latest prediction
            enriched = []
            for machine in machines:
                latest = await MachineService.get_latest_prediction_summary(
                    machine["id"]
                )
                enriched.append({**machine, **latest})

            return enriched

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching machines: {str(e)}"
            )


    @staticmethod
    async def get_machine(machine_id: UUID, plant_id: str) -> dict:
        """
        Fetches a single machine, verifying it belongs to the user's plant.
        This is the plant-level authorization check.

        If the machine exists but belongs to a different plant → 404
        We return 404 (not 403) to avoid leaking that the machine exists.
        """
        try:
            response = supabase.table("machines") \
                .select("*") \
                .eq("id", str(machine_id)) \
                .eq("plant_id", plant_id) \
                .single() \
                .execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Machine {machine_id} not found."
                )

            return response.data

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine {machine_id} not found."
            )


    @staticmethod
    async def get_latest_prediction_summary(machine_id: str) -> dict:
        """
        Fetches only the most recent prediction for a machine.
        Returns empty health data if no predictions exist yet.
        """
        try:
            response = supabase.table("predictions") \
                .select(
                    "failure_probability, health_score, alert_level, "
                    "primary_failure_mode, rul_cycles, predicted_at"
                ) \
                .eq("machine_id", machine_id) \
                .order("predicted_at", desc=True) \
                .limit(1) \
                .execute()

            if response.data:
                pred = response.data[0]
                return {
                    "health_score"        : pred.get("health_score"),
                    "alert_level"         : pred.get("alert_level"),
                    "failure_probability" : pred.get("failure_probability"),
                    "rul_cycles"          : pred.get("rul_cycles"),
                    "last_predicted_at"   : pred.get("predicted_at"),
                    "primary_failure_mode": pred.get("primary_failure_mode")
                }

        except Exception:
            pass

        # No predictions yet — return empty state
        return {
            "health_score"        : None,
            "alert_level"         : "UNKNOWN",
            "failure_probability" : None,
            "rul_cycles"          : None,
            "last_predicted_at"   : None,
            "primary_failure_mode": None
        }


    @staticmethod
    async def get_plant_summary(plant_id: str) -> dict:
        """
        Returns counts of machines by alert level.
        Powers the dashboard header summary cards.
        """
        try:
            response = supabase.table("machines") \
                .select("id") \
                .eq("plant_id", plant_id) \
                .neq("status", "decommissioned") \
                .execute()

            machines = response.data or []
            total = len(machines)

            # Count by alert level from latest predictions
            counts = {
                "CRITICAL": 0, "HIGH": 0,
                "MEDIUM"  : 0, "LOW" : 0,
                "NORMAL"  : 0, "UNKNOWN": 0
            }

            for machine in machines:
                summary = await MachineService.get_latest_prediction_summary(
                    machine["id"]
                )
                level = summary.get("alert_level", "UNKNOWN") or "UNKNOWN"
                counts[level] = counts.get(level, 0) + 1

            return {
                "total_machines" : total,
                "critical_count" : counts.get("CRITICAL", 0),
                "high_count"     : counts.get("HIGH", 0),
                "medium_count"   : counts.get("MEDIUM", 0),
                "normal_count"   : counts.get("NORMAL", 0) + counts.get("LOW", 0),
                "offline_count"  : 0
            }

        except Exception as e:
            return {
                "total_machines": 0,
                "critical_count": 0,
                "high_count"    : 0,
                "medium_count"  : 0,
                "normal_count"  : 0,
                "offline_count" : 0
            }