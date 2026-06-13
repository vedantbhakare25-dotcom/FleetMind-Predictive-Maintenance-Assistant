# Feature engineering for AI4I dataset (temp_diff, power, tool_wear_torque, quality_encoded) and CMAPSS dataset (rolling mean/std over 30 cycles, drop zero-variance sensors, clip RUL at 125), fits and transforms using saved scaler
# Preprocessing pipeline for FleetMind ML inference
# Handles feature engineering and scaling for AI4I dataset

import numpy as np
import pandas as pd
import joblib
import os
from pathlib import Path


#Constants

# Exact column order the scaler was fit on during training

FEATURE_COLS = [
    'Air temperature_K',
    'Process temperature_K',
    'Rotational speed_rpm',
    'Torque_nm',
    'Tool wear_min',
    'temp_diff',
    'power',
    'tool_wear_torque',
    'quality_encoded'
]

# Quality variant mapping
#The dataset contains machine quality grades:

"""
H = High
M = Medium
L = Low
"""
QUALITY_MAP = {'H': 2, 'M': 1, 'L': 0} 

# Path to the models directory
MODELS_DIR = Path(__file__).parent / 'models'


# ── Preprocessor Class ─────────────────────────────────────────────────────────

class AI4IPreprocessor:
    """
    Transforms raw sensor readings into scaled feature vectors
    ready for XGBoost inference.

    Usage:
        preprocessor = AI4IPreprocessor()          # load scaler once
        features = preprocessor.transform(data)    # call many times
    """

    def __init__(self):
        """
        Loads the fitted StandardScaler from disk.
        Called once when FastAPI starts up.
        """
        scaler_path = MODELS_DIR / 'scaler_ai4i.joblib'

        if not scaler_path.exists():
            raise FileNotFoundError(
                f"Scaler not found at {scaler_path}. "
                f"Run the training notebook first."
            )

        self.scaler = joblib.load(scaler_path)
        self.feature_cols = FEATURE_COLS
        print(f"✅ AI4IPreprocessor loaded scaler from {scaler_path}")


    def transform(self, raw_data: dict, quality_variant: str = 'M') -> pd.DataFrame:
        """
        Takes a raw sensor reading dictionary and returns a scaled
        feature DataFrame ready for model inference.

        Args:
            raw_data: dict with keys matching sensor column names
                Example: {
                    'Air temperature_K': 298.7,
                    'Process temperature_K': 308.2,
                    'Rotational speed_rpm': 1423.0,
                    'Torque_nm': 48.3,
                    'Tool wear_min': 176.0
                }
            quality_variant: 'H', 'M', or 'L' — from machine config

        Returns:
            pd.DataFrame with shape (1, 9) — one row, nine features, scaled
        """

        #Step 1: Validate inputs
        required_raw = [
            'Air temperature_K',
            'Process temperature_K',
            'Rotational speed_rpm',
            'Torque_nm',
            'Tool wear_min'
        ]

        missing = [col for col in required_raw if col not in raw_data]
        if missing:
            raise ValueError(f"Missing required sensor columns: {missing}")

        if quality_variant not in QUALITY_MAP:
            raise ValueError(f"quality_variant must be H, M, or L. Got: {quality_variant}")


        #Step 2: Extract raw sensor values
        air_temp    = float(raw_data['Air temperature_K'])
        proc_temp   = float(raw_data['Process temperature_K'])
        rpm         = float(raw_data['Rotational speed_rpm'])
        torque      = float(raw_data['Torque_nm'])
        tool_wear   = float(raw_data['Tool wear_min'])


        #Step 3: Engineer derived features
        # These formulas must exactly match the training notebook

        # temp_diff: cooling gap between process and ambient
        # Low values indicate heat dissipation failure risk
        temp_diff = proc_temp - air_temp

        # power: actual mechanical power in watts
        # 2π/60 converts rpm to radians per second
        power = torque * rpm * (2 * np.pi / 60)

        # tool_wear_torque: mechanical overload signal
        # High values indicate overstrain failure risk
        tool_wear_torque = tool_wear * torque

        # quality_encoded: numerical encoding of machine quality
        quality_encoded = QUALITY_MAP[quality_variant]


        #Step 4: Build feature row in exact training column order ───────────
        # Column order is critical — scaler expects this exact sequence
        feature_row = {
            'Air temperature_K'      : air_temp,
            'Process temperature_K'  : proc_temp,
            'Rotational speed_rpm'   : rpm,
            'Torque_nm'              : torque,
            'Tool wear_min'          : tool_wear,
            'temp_diff'                : temp_diff,
            'power'                    : power,
            'tool_wear_torque'         : tool_wear_torque,
            'quality_encoded'          : quality_encoded
        }

        df = pd.DataFrame([feature_row])[self.feature_cols]


        #Step 5: Apply scaling ──────────────────────────────────────────────
        # transform() not fit_transform() — scaler parameters are already fixed
        scaled_array = self.scaler.transform(df)
        scaled_df = pd.DataFrame(scaled_array, columns=self.feature_cols)

        return scaled_df


    def transform_batch(self, readings: list[dict], quality_variant: str = 'M') -> pd.DataFrame:
        """
        Transforms multiple sensor readings at once.
        Used by the CMAPSS RUL preprocessor for rolling window features.

        Args:
            readings: list of raw sensor dicts, ordered oldest → newest
            quality_variant: machine quality variant

        Returns:
            pd.DataFrame with shape (n, 9) — n rows, nine features, scaled
        """

        if len(readings) == 0:
            raise ValueError("readings list cannot be empty")

        rows = []
        for reading in readings:
            # Engineer features for each reading
            air_temp  = float(reading['Air temperature_K'])
            proc_temp = float(reading['Process temperature_K'])
            rpm       = float(reading['Rotational speed_rpm'])
            torque    = float(reading['Torque_nm'])
            tool_wear = float(reading['Tool wear_min'])

            rows.append({
                'Air temperature_K'     : air_temp,
                'Process temperature_K' : proc_temp,
                'Rotational speed_rpm'  : rpm,
                'Torque_nm'             : torque,
                'Tool wear_min'         : tool_wear,
                'temp_diff'               : proc_temp - air_temp,
                'power'                   : torque * rpm * (2 * np.pi / 60),
                'tool_wear_torque'        : tool_wear * torque,
                'quality_encoded'         : QUALITY_MAP.get(quality_variant, 1)
            })

        df = pd.DataFrame(rows)[self.feature_cols]
        scaled_array = self.scaler.transform(df)
        return pd.DataFrame(scaled_array, columns=self.feature_cols)


    def get_raw_features(self, raw_data: dict, quality_variant: str = 'M') -> dict:
        """
        Returns engineered but UNSCALED features.
        Used by root_cause.py which needs actual physical values,
        not scaled numbers, for threshold comparisons.

        Example: temp_diff=7.2 is meaningful. temp_diff=-1.3 (scaled) is not.
        """

        air_temp  = float(raw_data['Air temperature_K'])
        proc_temp = float(raw_data['Process temperature_K'])
        rpm       = float(raw_data['Rotational speed_rpm'])
        torque    = float(raw_data['Torque_nm'])
        tool_wear = float(raw_data['Tool wear_min'])

        return {
            'Air temperature_K'     : air_temp,
            'Process temperature_K' : proc_temp,
            'Rotational speed_rpm'  : rpm,
            'Torque_nm'             : torque,
            'Tool wear_min'         : tool_wear,
            'temp_diff'               : proc_temp - air_temp,
            'power'                   : torque * rpm * (2 * np.pi / 60),
            'tool_wear_torque'        : tool_wear * torque,
            'quality_encoded'         : QUALITY_MAP.get(quality_variant, 1)
        }