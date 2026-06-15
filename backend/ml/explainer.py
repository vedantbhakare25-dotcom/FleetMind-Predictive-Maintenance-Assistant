# SHAP-based explainability module for FleetMind
# Provides per-prediction feature contribution explanations

import joblib
import json
import numpy as np
import pandas as pd
import shap
from pathlib import Path


MODELS_DIR = Path(__file__).parent / 'models'

FEATURE_DISPLAY_NAMES = {
    'air_temperature'    : 'Air Temperature',
    'process_temperature': 'Process Temperature',
    'rotational_speed'   : 'Rotational Speed',
    'torque'             : 'Torque',
    'tool_wear'          : 'Tool Wear',
    'temp_diff'          : 'Cooling Gap (temp_diff)',
    'power'              : 'Mechanical Power',
    'tool_wear_torque'   : 'Wear-Torque Load',
    'quality_encoded'    : 'Machine Quality'
}


class FleetMindExplainer:
    """
    Generates SHAP-based explanations for failure predictions.
    Initialized once at FastAPI startup.
    """

    def __init__(self):
        model_path = MODELS_DIR / 'failure_classifier.joblib'
        if not model_path.exists():
            raise FileNotFoundError(
                "failure_classifier.joblib not found. "
                "Run 02_ai4i_training.ipynb first."
            )

        model = joblib.load(model_path)

        # Use default raw margin output
        # model_output='probability' conflicts with tree_path_dependent
        self.explainer = shap.TreeExplainer(model)

        # Convert raw log-odds expected value to probability via sigmoid
        # Raw value ~3.35 → probability ~0.034 (matches 3.4% failure rate)
       # Store raw expected value for shap_sum calculation in explain()
        ev = self.explainer.expected_value
        if hasattr(ev, '__len__'):
            # Binary classifier returns array [neg_class_ev, pos_class_ev]
            # We store both but use pos_class for margin calculations
            self._raw_expected = float(ev[1]) if len(ev) > 1 else float(ev[0])
        else:
            self._raw_expected = float(ev)

        # Use known dataset failure rate as baseline — more meaningful than
        # SHAP's expected value which reflects SMOTE-balanced training data
        # 339 failures / 10000 rows = 0.0339
        self.expected_value = 0.034

        # Load feature columns from saved metadata
        meta_path = MODELS_DIR / 'shap_metadata.json'
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            self.feature_cols = meta['feature_columns']
        else:
            self.feature_cols = list(FEATURE_DISPLAY_NAMES.keys())

        print(f"leetMindExplainer initialized")
        print(f"   Raw expected value  : {self._raw_expected:.4f}")
        print(f"   Prob expected value : {self.expected_value:.4f}  (should be ~0.034)")


    def explain(self, scaled_features: pd.DataFrame) -> dict:
        """
        Generates SHAP explanation for one prediction.

        Args:
            scaled_features: pd.DataFrame (1, 9) from AI4IPreprocessor.transform()

        Returns:
            dict with baseline, contributions per feature, top_factors,
            risk_factors, protective_factors
        """

        # ── Compute SHAP values ────────────────────────────────────────────────
        # Values are in raw margin space (log-odds)
        # Direction is still valid: positive = increases failure risk
        shap_values = self.explainer.shap_values(scaled_features)
        sample_shap = shap_values[0]  # shape (9,) for single sample


        # ── Build contributions dict ───────────────────────────────────────────
        contributions = {}
        total_abs_shap = sum(abs(v) for v in sample_shap)

        for feature_name, shap_val in zip(self.feature_cols, sample_shap):
            display_name = FEATURE_DISPLAY_NAMES.get(feature_name, feature_name)
            shap_float = float(shap_val)
            direction = 'RISK' if shap_float > 0 else 'PROTECTIVE'

          # NEW
            percentage = round(
                float((abs(shap_float) / total_abs_shap * 100)) if total_abs_shap > 0 else 0.0,
                1
            )

            contributions[display_name] = {
                'shap_value' : round(shap_float, 4),
                'direction'  : direction,
                'percentage' : percentage,
                'raw_key'    : feature_name
            }


        # ── Sort by absolute impact ────────────────────────────────────────────
        sorted_contributions = dict(
            sorted(
                contributions.items(),
                key=lambda x: abs(x[1]['shap_value']),
                reverse=True
            )
        )


        # ── Top 3 factors for UI panel ─────────────────────────────────────────
        top_factors = [
            {
                'feature'    : name,
                'shap_value' : data['shap_value'],
                'direction'  : data['direction'],
                'percentage' : data['percentage']
            }
            for name, data in list(sorted_contributions.items())[:3]
        ]


        # ── Risk vs Protective split ───────────────────────────────────────────
        risk_factors = [
            {'feature': name, **data}
            for name, data in sorted_contributions.items()
            if data['direction'] == 'RISK'
        ]

        protective_factors = [
            {'feature': name, **data}
            for name, data in sorted_contributions.items()
            if data['direction'] == 'PROTECTIVE'
        ]


        # ── Validation: convert raw margin prediction to probability ───────────
        # baseline (prob) + shap_sum would be wrong since shap is in margin space
        # Instead: sigmoid(raw_expected + shap_sum) gives the correct probability
     # prediction_from_shap is a sanity check only
# The actual prediction probability comes from predictor.predict_failure()
        shap_sum = float(np.sum(sample_shap))
        raw_prediction = self._raw_expected + shap_sum
        prediction_from_shap = round(float(1 / (1 + np.exp(-raw_prediction))), 4)
        return {
            'baseline'             : round(self.expected_value, 4),
            'prediction_from_shap' : prediction_from_shap,
            'contributions'        : sorted_contributions,
            'top_factors'          : top_factors,
            'risk_factors'         : risk_factors,
            'protective_factors'   : protective_factors
        }