# Loads trained joblib models at import time, exposes predict_failure(), predict_failure_modes(), predict_rul() functions used by prediction_service
# Production inference engine for FleetMind
# Loads all trained models and exposes clean prediction functions

import joblib
import json
import numpy as np
import pandas as pd
from pathlib import Path


MODELS_DIR = Path(__file__).parent / 'models'

# RUL cap — same value used during CMAPSS training
RUL_MAX_CYCLES = 125

# Average cycle duration in hours (assumption for FleetMind demo)
# In production this would come from machine configuration
HOURS_PER_CYCLE = 2.0


class FleetMindPredictor:
    """
    Central inference class for all FleetMind ML models.
    Initialized once at FastAPI startup, reused for every request.
    """

    def __init__(self):
        """
        Loads all trained models and configuration from disk.
        Raises clear errors if any model file is missing.
        """
        print("Loading FleetMind ML models...")
        self._load_failure_model()
        self._load_failure_mode_models()
        self._load_threshold_config()
        print(" models loaded")


    def _load_failure_model(self):
        """Loads the main binary failure classifier."""
        path = MODELS_DIR / 'failure_classifier.joblib'
        if not path.exists():
            raise FileNotFoundError(
                f"failure_classifier.joblib not found. "
                f"Run 02_ai4i_training.ipynb first."
            )
        self.failure_model = joblib.load(path)
        print(f"failure_classifier loaded")


    def _load_failure_mode_models(self):
        """Loads one classifier per failure mode."""
        self.mode_models = {}
        modes = ['TWF', 'HDF', 'PWF', 'OSF']

        for mode in modes:
            path = MODELS_DIR / f'failure_mode_{mode}.joblib'
            if not path.exists():
                raise FileNotFoundError(
                    f"failure_mode_{mode}.joblib not found."
                )
            self.mode_models[mode] = joblib.load(path)
            print(f"failure_mode_{mode} loaded")


    def _load_threshold_config(self):
        """
        Loads threshold values from JSON config.
        Thresholds are stored in JSON (not hardcoded) so they
        can be updated without redeploying code.
        """
        path = MODELS_DIR / 'threshold_config.json'
        if not path.exists():
            # Fallback defaults if config file missing
            self.failure_threshold = 0.50
            self.mode_thresholds = {m: 0.50 for m in ['TWF', 'HDF', 'PWF', 'OSF']}
            print("threshold_config.json not found — using defaults")
            return

        with open(path) as f:
            config = json.load(f)

        self.failure_threshold = config['failure_prediction']['threshold']
        self.mode_thresholds = config['failure_modes']
        print(f"Thresholds loaded — failure threshold: {self.failure_threshold}")


    #Public Prediction Methods

    def predict_failure(self, scaled_features: pd.DataFrame) -> dict:
        """
        Predicts failure probability for a single machine observation.

        Args:
            scaled_features: pd.DataFrame with shape (1, 9)
                             Output of AI4IPreprocessor.transform()

        Returns:
            dict: {
                'probability': 0.87,        # raw model output
                'predicted': True,          # threshold applied
                'confidence': 'HIGH'        # human label
            }
        """

        # predict_proba returns [[prob_class_0, prob_class_1]]
        # We want prob_class_1 — the probability of failure
        proba_array = self.failure_model.predict_proba(scaled_features)
        failure_prob = float(proba_array[0][1])

        # Apply tuned threshold (not hardcoded 0.5)
        predicted = failure_prob >= self.failure_threshold

        # Confidence label for UI display
        confidence = self._probability_to_confidence(failure_prob)

        return {
            'probability': round(failure_prob, 4),
            'predicted': bool(predicted),
            'confidence': confidence
        }


    def predict_failure_modes(self, scaled_features: pd.DataFrame) -> dict:
        """
        Predicts probability for each failure mode independently.

        Returns:
            dict: {
                'TWF': 0.12,
                'HDF': 0.78,
                'PWF': 0.34,
                'OSF': 0.09,
                'primary_mode': 'HDF',
                'active_modes': ['HDF', 'PWF']
            }
        """

        mode_probs = {}

        for mode, model in self.mode_models.items():
            proba = model.predict_proba(scaled_features)[0][1]
            mode_probs[mode] = round(float(proba), 4)

        # Primary mode: highest probability failure mode
        primary_mode = max(mode_probs, key=mode_probs.get)

        # Active modes: any mode above its threshold
        active_modes = [
            mode for mode, prob in mode_probs.items()
            if prob >= self.mode_thresholds.get(mode, 0.50)
        ]

        return {
            **mode_probs,                      # TWF: 0.12, HDF: 0.78, etc.
            'primary_mode': primary_mode,
            'active_modes': active_modes
        }


    def predict_rul(self, tool_wear: float, failure_prob: float) -> dict:
        """
        Estimates Remaining Useful Life.

        For FleetMind V1 we use a physics-informed heuristic
        instead of the CMAPSS model directly, because:
        - AI4I data doesn't have engine cycle trajectories
        - The CMAPSS model expects 30-cycle rolling window history
        - For demo purposes, RUL is derived from tool_wear + failure_prob

        In production with real IoT streams, replace this with
        the trained CMAPSS XGBoost regressor.

        Args:
            tool_wear: current tool wear in minutes (0-253)
            failure_prob: failure probability from predict_failure()

        Returns:
            dict: {
                'cycles_remaining': 23,
                'hours_remaining': 46.0,
                'trend': 'DECLINING',
                'rul_normalized': 0.18
            }
        """

        # Tool wear max in AI4I is 253 minutes
        TOOL_WEAR_MAX = 253.0

        # Normalize tool wear to 0-1 degradation signal
        wear_degradation = min(tool_wear / TOOL_WEAR_MAX, 1.0)

        # Combine tool wear degradation and failure probability
        # Both signal proximity to failure — weighted combination
        combined_degradation = (0.6 * wear_degradation) + (0.4 * failure_prob)
        combined_degradation = min(combined_degradation, 1.0)

        # Map to RUL cycles (inverse of degradation)
        rul_normalized = 1.0 - combined_degradation
        rul_cycles = int(rul_normalized * RUL_MAX_CYCLES)

        # Convert to hours
        rul_hours = round(rul_cycles * HOURS_PER_CYCLE, 1)

        # Trend label based on failure probability
        if failure_prob >= 0.75:
            trend = 'CRITICAL_DECLINE'
        elif failure_prob >= 0.50:
            trend = 'DECLINING'
        elif failure_prob >= 0.30:
            trend = 'GRADUAL_DECLINE'
        else:
            trend = 'STABLE'

        return {
            'cycles_remaining': rul_cycles,
            'hours_remaining': rul_hours,
            'trend': trend,
            'rul_normalized': round(rul_normalized, 4)
        }


    #Private Helper Methods

    def _probability_to_confidence(self, prob: float) -> str:
        """
        Maps failure probability to a human-readable confidence label.
        Used in the UI to display alongside the percentage.
        """
        if prob >= 0.90:
            return 'VERY HIGH'
        elif prob >= 0.75:
            return 'HIGH'
        elif prob >= 0.50:
            return 'MEDIUM'
        elif prob >= 0.30:
            return 'LOW'
        else:
            return 'VERY LOW'