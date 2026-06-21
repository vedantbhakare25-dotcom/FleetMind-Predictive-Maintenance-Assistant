# Production inference engine for FleetMind
# Loads all trained models and exposes clean prediction functions

import joblib
import json
import numpy as np
import pandas as pd
from pathlib import Path


MODELS_DIR = Path(__file__).parent / 'models'

RUL_MAX_CYCLES = 125
HOURS_PER_CYCLE = 2.0


class FleetMindPredictor:
    """
    Central inference class for all FleetMind ML models.
    Initialized once at FastAPI startup, reused for every request.
    """

    def __init__(self):
        print("Loading FleetMind ML models...")
        self._load_failure_model()
        self._load_failure_mode_models()
        self._load_threshold_config()
        print("  All models loaded successfully")


    def _load_failure_model(self):
        path = MODELS_DIR / 'failure_classifier.joblib'
        if not path.exists():
            raise FileNotFoundError(
                "failure_classifier.joblib not found. "
                "Run 02_ai4i_training.ipynb first."
            )
        self.failure_model = joblib.load(path)
        print("    failure_classifier loaded")


    def _load_failure_mode_models(self):
        self.mode_models = {}
        for mode in ['TWF', 'HDF', 'PWF', 'OSF']:
            path = MODELS_DIR / f'failure_mode_{mode}.joblib'
            if not path.exists():
                raise FileNotFoundError(f"failure_mode_{mode}.joblib not found.")
            self.mode_models[mode] = joblib.load(path)
            print(f"    failure_mode_{mode} loaded")


    def _load_threshold_config(self):
        path = MODELS_DIR / 'threshold_config.json'
        if not path.exists():
            self.failure_threshold = 0.50
            self.mode_thresholds = {m: 0.50 for m in ['TWF', 'HDF', 'PWF', 'OSF']}
            print("  ⚠️  threshold_config.json not found — using defaults")
            return

        with open(path) as f:
            config = json.load(f)

        self.failure_threshold = config['failure_prediction']['threshold']
        self.mode_thresholds = config['failure_modes']
        print(f"    Thresholds loaded — failure threshold: {self.failure_threshold}")


    def predict_failure(self, scaled_features: pd.DataFrame) -> dict:
        """
        Args:
            scaled_features: output of AI4IPreprocessor.transform()
                             DataFrame shape (1, 9) with columns:
                             air_temperature, process_temperature, etc.

        Returns:
            {'probability': 0.87, 'predicted': True, 'confidence': 'HIGH'}
        """
        proba_array = self.failure_model.predict_proba(scaled_features)
        failure_prob = float(proba_array[0][1])
        predicted = failure_prob >= self.failure_threshold
        confidence = self._probability_to_confidence(failure_prob)

        return {
            'probability' : round(failure_prob, 4),
            'predicted'   : bool(predicted),
            'confidence'  : confidence
        }


    def predict_failure_modes(self, scaled_features: pd.DataFrame) -> dict:
        """
        Returns probability for each failure mode independently.

        Returns:
            {
                'TWF': 0.12, 'HDF': 0.78, 'PWF': 0.34, 'OSF': 0.09,
                'primary_mode': 'HDF',
                'active_modes': ['HDF']
            }
        """
        mode_probs = {}
        for mode, model in self.mode_models.items():
            proba = model.predict_proba(scaled_features)[0][1]
            mode_probs[mode] = round(float(proba), 4)

        primary_mode = max(mode_probs, key=mode_probs.get)
        active_modes = [
            mode for mode, prob in mode_probs.items()
            if prob >= self.mode_thresholds.get(mode, 0.50)
        ]

        return {
            **mode_probs,
            'primary_mode' : primary_mode,
            'active_modes' : active_modes
        }


    def predict_rul(self, tool_wear: float, failure_prob: float) -> dict:
        """
        Estimates Remaining Useful Life using tool wear + failure probability.

        Args:
            tool_wear: current tool_wear value (0 to 253)
            failure_prob: from predict_failure()['probability']

        Returns:
            {'cycles_remaining': 23, 'hours_remaining': 46.0, 'trend': 'DECLINING', ...}
        """
        TOOL_WEAR_MAX = 253.0

        wear_degradation = min(tool_wear / TOOL_WEAR_MAX, 1.0)
        combined_degradation = min(
            (0.6 * wear_degradation) + (0.4 * failure_prob),
            1.0
        )

        rul_normalized = 1.0 - combined_degradation
        rul_cycles = int(rul_normalized * RUL_MAX_CYCLES)
        rul_hours = round(rul_cycles * HOURS_PER_CYCLE, 1)

        if failure_prob >= 0.75:
            trend = 'CRITICAL_DECLINE'
        elif failure_prob >= 0.50:
            trend = 'DECLINING'
        elif failure_prob >= 0.30:
            trend = 'GRADUAL_DECLINE'
        else:
            trend = 'STABLE'

        return {
            'cycles_remaining' : rul_cycles,
            'hours_remaining'  : rul_hours,
            'trend'            : trend,
            'rul_normalized'   : round(rul_normalized, 4)
        }


    def _probability_to_confidence(self, prob: float) -> str:
        if prob >= 0.90:   return 'VERY HIGH'
        elif prob >= 0.75: return 'HIGH'
        elif prob >= 0.50: return 'MEDIUM'
        elif prob >= 0.30: return 'LOW'
        else:              return 'VERY LOW'