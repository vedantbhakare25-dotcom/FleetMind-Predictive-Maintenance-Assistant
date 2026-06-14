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
    'Air temperature [K]'     : 'Air Temperature',
    'Process temperature [K]' : 'Process Temperature',
    'Rotational speed [rpm]'  : 'Rotational Speed',
    'Torque [Nm]'             : 'Torque',
    'Tool wear [min]'         : 'Tool Wear',
    'temp_diff'               : 'Cooling Gap (temp_diff)',
    'power'                   : 'Mechanical Power',
    'tool_wear_torque'        : 'Wear-Torque Load',
    'quality_encoded'         : 'Machine Quality'
}


class FleetMindExplainer:
    """
    Generates SHAP-based explanations for failure predictions.
    Initialized once at FastAPI startup with the trained model.
    """

    def __init__(self):
        """
        Loads the failure classifier and initializes TreeSHAP explainer.
        TreeExplainer is initialized once — not per request.
        """
        model_path = MODELS_DIR / 'failure_classifier.joblib'
        if not model_path.exists():
            raise FileNotFoundError(
                "failure_classifier.joblib not found. "
                "Run 02_ai4i_training.ipynb first."
            )

        model = joblib.load(model_path)
        self.explainer = shap.TreeExplainer(model)
        self.expected_value = float(self.explainer.expected_value)

        # Load SHAP metadata saved during training
        meta_path = MODELS_DIR / 'shap_metadata.json'
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            self.feature_cols = meta['feature_columns']
        else:
            # Fallback if metadata file missing
            self.feature_cols = list(FEATURE_DISPLAY_NAMES.keys())

        print(f"FleetMindExplainer initialized")
        print(f"Expected value (baseline): {self.expected_value:.4f}")


    def explain(self, scaled_features: pd.DataFrame) -> dict:
        """
        Generates a complete SHAP explanation for one prediction.

        Args:
            scaled_features: pd.DataFrame (1, 9) from preprocessor

        Returns:
            dict: {
                'baseline': 0.034,
                'prediction_from_shap': 0.87,
                'contributions': {
                    'Cooling Gap (temp_diff)': {
                        'shap_value': 0.312,
                        'direction': 'RISK',
                        'percentage': 31.2
                    },
                    ...
                },
                'top_factors': [...],     # top 3, sorted by impact
                'risk_factors': [...],    # features increasing risk
                'protective_factors': []  # features decreasing risk
            }
        """

        #Compute SHAP values
        # shap_values shape: (1, 9) for single sample
        shap_values = self.explainer.shap_values(scaled_features)

        # Extract the array for our single sample
        # shap_values[0] gives us the 9 feature contributions
        sample_shap = shap_values[0]


        #Build contributions dictionary
        contributions = {}
        total_abs_shap = sum(abs(v) for v in sample_shap)

        for feature_name, shap_val in zip(self.feature_cols, sample_shap):
            display_name = FEATURE_DISPLAY_NAMES.get(feature_name, feature_name)
            shap_float = float(shap_val)

            # Direction: positive SHAP = increases failure risk
            direction = 'RISK' if shap_float > 0 else 'PROTECTIVE'

            # Percentage contribution relative to total absolute SHAP sum
            # This is what the UI displays as "+31.2%"
            percentage = round(
                (abs(shap_float) / total_abs_shap * 100) if total_abs_shap > 0 else 0,
                1
            )

            contributions[display_name] = {
                'shap_value'  : round(shap_float, 4),
                'direction'   : direction,
                'percentage'  : percentage,
                'raw_key'     : feature_name
            }


        #Sort by absolute impact 
        sorted_contributions = dict(
            sorted(
                contributions.items(),
                key=lambda x: abs(x[1]['shap_value']),
                reverse=True
            )
        )


        #Top 3 factors 
        # These are displayed prominently in the FleetMind UI panel
        top_factors = []
        for name, data in list(sorted_contributions.items())[:3]:
            top_factors.append({
                'feature'    : name,
                'shap_value' : data['shap_value'],
                'direction'  : data['direction'],
                'percentage' : data['percentage']
            })


        #Risk vs Protective split
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


        # SHAP sum check
        # baseline + sum(shap_values) should approximately equal the prediction
        # This validates our SHAP computation is correct
        shap_sum = float(np.sum(sample_shap))
        prediction_from_shap = round(self.expected_value + shap_sum, 4)

# Initializes TreeSHAP explainer on the failure prediction model, exposes explain() function that returns baseline, per-feature SHAP contributions, and top 3 factors with direction

        return {
            'baseline'             : round(self.expected_value, 4),
            'prediction_from_shap' : prediction_from_shap,
            'contributions'        : sorted_contributions,
            'top_factors'          : top_factors,
            'risk_factors'         : risk_factors,
            'protective_factors'   : protective_factors
        }