# Preprocessing pipeline for FleetMind ML inference
# Handles feature engineering and scaling for AI4I dataset
'''
  preprocessor.py  → cleans sensor data
  predictor.py     → predicts failure
  explainer.py     → explains why
  health_score.py  → calculates score
  root_cause.py    → generates text
  
  '''
import numpy as np
import pandas as pd
import joblib
from pathlib import Path


# ── Constants ──────────────────────────────────────────────────────────────────

# These MUST exactly match FEATURE_COLS in 02_ai4i_training.ipynb
# Your CSV has cleaned column names without brackets
FEATURE_COLS = [
    'air_temperature',
    'process_temperature',
    'rotational_speed',
    'torque',
    'tool_wear',
    'temp_diff',
    'power',
    'tool_wear_torque',
    'quality_encoded'
]

# Keys that must be present in the raw_data dict passed to transform()
REQUIRED_RAW_COLS = [
    'air_temperature',
    'process_temperature',
    'rotational_speed',
    'torque',
    'tool_wear'
]

QUALITY_MAP = {'H': 2, 'M': 1, 'L': 0}

MODELS_DIR = Path(__file__).parent / 'models'


# ── Preprocessor Class ─────────────────────────────────────────────────────────

class AI4IPreprocessor:
    """
    Transforms raw sensor readings into scaled feature vectors
    ready for XGBoost inference.

    Usage:
        preprocessor = AI4IPreprocessor()
        features = preprocessor.transform(data)
    """

    def __init__(self):
        scaler_path = MODELS_DIR / 'scaler_ai4i.joblib'

        if not scaler_path.exists():
            raise FileNotFoundError(
                f"Scaler not found at {scaler_path}. "
                f"Run 02_ai4i_training.ipynb first."
            )

        self.scaler = joblib.load(scaler_path)
        self.feature_cols = FEATURE_COLS
        print(f"  AI4IPreprocessor loaded scaler from {scaler_path}")


    def transform(self, raw_data: dict, quality_variant: str = 'M') -> pd.DataFrame:
        """
        Takes raw sensor dict → returns scaled feature DataFrame (1, 9).

        Args:
            raw_data: dict with keys matching REQUIRED_RAW_COLS
                Example: {
                    'air_temperature': 298.7,
                    'process_temperature': 308.2,
                    'rotational_speed': 1423.0,
                    'torque': 48.3,
                    'tool_wear': 176.0
                }
            quality_variant: 'H', 'M', or 'L'

        Returns:
            pd.DataFrame shape (1, 9) — scaled, ready for model inference
        """

        # ── Validate ───────────────────────────────────────────────────────────
        missing = [c for c in REQUIRED_RAW_COLS if c not in raw_data]
        if missing:
            raise ValueError(f"Missing required sensor columns: {missing}")

        if quality_variant not in QUALITY_MAP:
            raise ValueError(f"quality_variant must be H, M, or L. Got: {quality_variant}")

        # ── Extract raw values ─────────────────────────────────────────────────
        air_temp  = float(raw_data['air_temperature'])
        proc_temp = float(raw_data['process_temperature'])
        rpm       = float(raw_data['rotational_speed'])
        torque    = float(raw_data['torque'])
        tool_wear = float(raw_data['tool_wear'])

        # ── Engineer derived features ──────────────────────────────────────────
        # Formulas match exactly what was used in 02_ai4i_training.ipynb
        temp_diff        = proc_temp - air_temp
        power            = torque * rpm * (2 * np.pi / 60)
        tool_wear_torque = tool_wear * torque
        quality_encoded  = QUALITY_MAP[quality_variant]

        # ── Build feature row in exact training column order ───────────────────
        feature_row = {
            'air_temperature'      : air_temp,
            'process_temperature'  : proc_temp,
            'rotational_speed'   : rpm,
            'torque'              : torque,
            'tool_wear'          : tool_wear,
            'temp_diff'              : temp_diff,
            'power'                  : power,
            'tool_wear_torque'       : tool_wear_torque,
            'quality_encoded'        : quality_encoded
        }

        df = pd.DataFrame([feature_row])[self.feature_cols]

        # ── Scale ──────────────────────────────────────────────────────────────
        scaled_array = self.scaler.transform(df)
        scaled_df = pd.DataFrame(scaled_array, columns=self.feature_cols)

        return scaled_df


    def transform_batch(self, readings: list, quality_variant: str = 'M') -> pd.DataFrame:
        """
        Transforms multiple sensor readings at once.
        readings: list of dicts, each matching REQUIRED_RAW_COLS
        """
        if not readings:
            raise ValueError("readings list cannot be empty")

        rows = []
        for r in readings:
            air_temp  = float(r['air_temperature'])
            proc_temp = float(r['process_temperature'])
            rpm       = float(r['rotational_speed'])
            torque    = float(r['torque'])
            tool_wear = float(r['tool_wear'])

            rows.append({
                'air_temperature'     : air_temp,
                'process_temperature' : proc_temp,
                'rotational_speed'  : rpm,
                'torque'             : torque,
                'tool_wear'         : tool_wear,
                'temp_diff'             : proc_temp - air_temp,
                'power'                 : torque * rpm * (2 * np.pi / 60),
                'tool_wear_torque'      : tool_wear * torque,
                'quality_encoded'       : QUALITY_MAP.get(quality_variant, 1)
            })

        df = pd.DataFrame(rows)[self.feature_cols]
        scaled_array = self.scaler.transform(df)
        return pd.DataFrame(scaled_array, columns=self.feature_cols)


    def get_raw_features(self, raw_data: dict, quality_variant: str = 'M') -> dict:
        """
        Returns engineered but UNSCALED features.
        Used by root_cause.py for physical threshold comparisons.
        e.g. temp_diff=7.2 is meaningful — scaled version is not.
        """
        air_temp  = float(raw_data['air_temperature'])
        proc_temp = float(raw_data['process_temperature'])
        rpm       = float(raw_data['rotational_speed'])
        torque    = float(raw_data['torque'])
        tool_wear = float(raw_data['tool_wear'])

        return {
            'air_temperature'     : air_temp,
            'process_temperature' : proc_temp,
            'rotational_speed'  : rpm,
            'torque'             : torque,
            'tool_wear'         : tool_wear,
            'temp_diff'             : proc_temp - air_temp,
            'power'                 : torque * rpm * (2 * np.pi / 60),
            'tool_wear_torque'      : tool_wear * torque,
            'quality_encoded'       : QUALITY_MAP.get(quality_variant, 1)
        }