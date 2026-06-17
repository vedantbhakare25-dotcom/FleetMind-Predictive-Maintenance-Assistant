# Core prediction pipeline orchestration
# Connects ML modules to database and alert system

from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status, Request
from app.db.supabase_client import supabase
from app.services.sensor_service import SensorService
from app.services.machine_service import MachineService
from app.services.alert_service import AlertService
from ml.health_score import calculate_health_score
from ml.root_cause import generate_root_cause


class PredictionService:

    @staticmethod
    async def run_full_pipeline(
        machine_id : UUID,
        plant_id   : str,
        request    : Request
    ) -> dict:
        """
        Runs the complete FleetMind prediction pipeline.

        Steps:
            1.  Verify machine belongs to user's plant
            2.  Fetch recent sensor readings from Supabase
            3.  Preprocess features (AI4I format)
            4.  Predict failure probability
            5.  Predict failure modes
            6.  Predict RUL
            7.  Generate SHAP explanation
            8.  Calculate health score
            9.  Generate root cause text
            10. Store prediction in Supabase
            11. Create alert if threshold crossed
            12. Return complete response

        Args:
            machine_id : UUID of the machine to predict for
            plant_id   : plant_id from authenticated user (for authorization)
            request    : FastAPI request object (to access app.state ML models)
        """

        # ── Step 1: Verify machine ownership ──────────────────────────────────
        machine = await MachineService.get_machine(machine_id, plant_id)
        machine_name    = machine["name"]
        quality_variant = machine.get("quality_variant", "M")


        # ── Step 2: Fetch sensor readings ──────────────────────────────────────
        readings = await SensorService.get_recent_readings(machine_id, limit=30)

        if not readings:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"No sensor readings found for machine '{machine_name}'. "
                    f"Post sensor data first via POST /api/sensors/readings."
                )
            )

        # Use the most recent reading for current state prediction
        latest_reading = readings[0]

        # Build raw sensor dict from the latest reading
        raw_sensor_data = {
            "air_temperature"    : latest_reading.get("air_temperature", 300.0),
            "process_temperature": latest_reading.get("process_temperature", 310.0),
            "rotational_speed"   : latest_reading.get("rotational_speed", 1500.0),
            "torque"             : latest_reading.get("torque", 40.0),
            "tool_wear"          : latest_reading.get("tool_wear", 0.0)
        }

        latest_reading_id = latest_reading.get("id")


        # ── Step 3: Get ML models from app.state ───────────────────────────────
        # Models were loaded once at startup — reuse them here
        preprocessor = request.app.state.preprocessor
        predictor    = request.app.state.predictor
        explainer    = request.app.state.explainer

        if not predictor:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML models not loaded. Check server logs."
            )


        # ── Step 4: Preprocess features ────────────────────────────────────────
        scaled_features = preprocessor.transform(
            raw_sensor_data,
            quality_variant=quality_variant
        )
        raw_features = preprocessor.get_raw_features(
            raw_sensor_data,
            quality_variant=quality_variant
        )


        # ── Step 5: Predict failure ────────────────────────────────────────────
        failure_result = predictor.predict_failure(scaled_features)
        failure_prob   = failure_result["probability"]
        failure_pred   = failure_result["predicted"]
        confidence     = failure_result["confidence"]


        # ── Step 6: Predict failure modes ──────────────────────────────────────
        modes_result = predictor.predict_failure_modes(scaled_features)


        # ── Step 7: Predict RUL ────────────────────────────────────────────────
        rul_result = predictor.predict_rul(
            tool_wear=raw_sensor_data["tool_wear"],
            failure_prob=failure_prob
        )


        # ── Step 8: SHAP explanation ───────────────────────────────────────────
        shap_result = explainer.explain(scaled_features)


        # ── Step 9: Health score ───────────────────────────────────────────────
        health_result = calculate_health_score(
            failure_prob=failure_prob,
            rul_cycles=rul_result["cycles_remaining"]
        )


        # ── Step 10: Root cause ────────────────────────────────────────────────
        root_cause_result = generate_root_cause(
            shap_explanation=shap_result,
            failure_modes=modes_result,
            raw_features=raw_features,
            failure_prob=failure_prob
        )


        # ── Step 11: Store prediction in Supabase ──────────────────────────────
        prediction_record = {
            "machine_id"          : str(machine_id),
            "sensor_reading_id"   : latest_reading_id,
            "failure_probability" : failure_prob,
            "failure_predicted"   : failure_pred,
            "health_score"        : health_result.score,
            "alert_level"         : health_result.level,
            "rul_cycles"          : rul_result["cycles_remaining"],
            "rul_hours"           : rul_result["hours_remaining"],
            "mode_twf_prob"       : modes_result.get("TWF"),
            "mode_hdf_prob"       : modes_result.get("HDF"),
            "mode_pwf_prob"       : modes_result.get("PWF"),
            "mode_osf_prob"       : modes_result.get("OSF"),
            "primary_failure_mode": modes_result.get("primary_mode"),
            "shap_values"         : shap_result.get("contributions"),
            "top_factors"         : shap_result.get("top_factors"),
            "root_cause_text"     : root_cause_result.detailed_text,
            "model_version"       : "1.0.0"
        }

        try:
            stored = supabase.table("predictions") \
                .insert(prediction_record) \
                .execute()
            stored_prediction = stored.data[0]
            prediction_id = stored_prediction["id"]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store prediction: {str(e)}"
            )


        # ── Step 12: Create alert if needed ───────────────────────────────────
        alert_created = False
        alert = await AlertService.create_alert(
            machine_id    = machine_id,
            prediction_id = UUID(prediction_id),
            health_level  = health_result.level,
            failure_prob  = failure_prob,
            root_cause    = root_cause_result.detailed_text,
            machine_name  = machine_name
        )
        if alert:
            alert_created = True


        # ── Step 13: Build and return complete response ────────────────────────
        return {
            "id"                  : prediction_id,
            "machine_id"          : str(machine_id),
            "predicted_at"        : stored_prediction.get("predicted_at"),
            "failure_probability" : failure_prob,
            "failure_predicted"   : failure_pred,
            "confidence"          : confidence,
            "health_score"        : {
                "score"             : health_result.score,
                "level"             : health_result.level,
                "recommendation"    : health_result.recommendation,
                "failure_component" : health_result.failure_component,
                "rul_component"     : health_result.rul_component
            },
            "failure_modes"       : modes_result,
            "rul"                 : rul_result,
            "explainability"      : shap_result,
            "root_cause"          : {
                "primary_cause"         : root_cause_result.primary_cause,
                "detailed_text"         : root_cause_result.detailed_text,
                "active_modes"          : root_cause_result.active_modes,
                "contributing_features" : root_cause_result.contributing_features,
                "confidence"            : root_cause_result.confidence,
                "action_required"       : root_cause_result.action_required
            },
            "alert_created"       : alert_created,
            "alert_level"         : health_result.level,
            "model_version"       : "1.0.0"
        }