# Root cause analysis module for FleetMind
# Combines SHAP explanations and failure mode probabilities
# to generate human-readable maintenance recommendations

from dataclasses import dataclass, field


PHYSICAL_THRESHOLDS = {
    'HDF': {
        'temp_diff_threshold' : 8.6,
        'rpm_threshold'       : 1380,
        'description'         : 'Heat Dissipation Failure'
    },
    'PWF': {
        'power_min'   : 3500,
        'power_max'   : 9000,
        'description' : 'Power Failure'
    },
    'OSF': {
        'description' : 'Overstrain Failure'
    },
    'TWF': {
        'tool_wear_threshold' : 200,
        'description'         : 'Tool Wear Failure'
    }
}

MODE_CONFIDENCE_THRESHOLD = 0.40


@dataclass
class RootCauseResult:
    primary_cause         : str
    detailed_text         : str
    active_modes          : list = field(default_factory=list)
    contributing_features : list = field(default_factory=list)
    confidence            : str = 'MEDIUM'
    action_required       : str = ''


def generate_root_cause(
    shap_explanation : dict,
    failure_modes    : dict,
    raw_features     : dict,
    failure_prob     : float
) -> RootCauseResult:
    """
    Args:
        shap_explanation : output of FleetMindExplainer.explain()
        failure_modes    : output of FleetMindPredictor.predict_failure_modes()
        raw_features     : UNSCALED dict from AI4IPreprocessor.get_raw_features()
                           Keys: 'air_temperature', 'torque', 'tool_wear', etc.
        failure_prob     : float from predict_failure()['probability']
    """

    # Machine is healthy — no root cause needed
    if failure_prob < 0.30:
        return RootCauseResult(
            primary_cause='No significant risk detected',
            detailed_text='Machine is operating within normal parameters. '
                          'No specific failure patterns identified.',
            active_modes=[],
            contributing_features=[],
            confidence='HIGH',
            action_required='Continue routine monitoring.'
        )

    # ── Identify active failure modes ──────────────────────────────────────────
    active_modes = [
        mode for mode in ['HDF', 'PWF', 'OSF', 'TWF']
        if failure_modes.get(mode, 0) >= MODE_CONFIDENCE_THRESHOLD
    ]

    mode_probs_only = {
        k: v for k, v in failure_modes.items()
        if k in ['HDF', 'PWF', 'OSF', 'TWF']
    }
    primary_mode = max(mode_probs_only, key=mode_probs_only.get)

    # ── Top contributing features from SHAP ───────────────────────────────────
    top_factors = shap_explanation.get('top_factors', [])
    contributing_features = [f['feature'] for f in top_factors]

    # ── Generate cause text per active mode ───────────────────────────────────
    cause_texts = []
    for mode in active_modes:
        text = _generate_mode_text(mode, raw_features, failure_modes.get(mode, 0))
        if text:
            cause_texts.append(text)

    if not cause_texts:
        cause_texts.append(
            "Multiple sensor parameters deviating from normal ranges. "
            "No single dominant failure mode identified — possible combined effect."
        )

    # ── Primary cause summary ──────────────────────────────────────────────────
    if active_modes:
        primary_desc = PHYSICAL_THRESHOLDS.get(primary_mode, {}).get('description', primary_mode)
        primary_cause = f"{primary_desc} risk — {int(failure_modes.get(primary_mode, 0)*100)}% probability"
    else:
        primary_cause = f"Elevated failure risk — {int(failure_prob*100)}% probability"

    # ── Confidence level ───────────────────────────────────────────────────────
    max_mode_prob = max(mode_probs_only.values()) if mode_probs_only else 0
    if max_mode_prob >= 0.75:   confidence = 'HIGH'
    elif max_mode_prob >= 0.50: confidence = 'MEDIUM'
    else:                       confidence = 'LOW'

    action = _generate_action(active_modes, failure_prob, raw_features)

    return RootCauseResult(
        primary_cause=primary_cause,
        detailed_text=' | '.join(cause_texts),
        active_modes=active_modes,
        contributing_features=contributing_features,
        confidence=confidence,
        action_required=action
    )


def _generate_mode_text(mode: str, raw_features: dict, mode_prob: float) -> str:
    """
    Uses actual unscaled sensor values to produce specific,
    actionable text — not generic descriptions.
    Keys match your CSV: 'tool_wear', 'torque', etc.
    """
    prob_pct = int(mode_prob * 100)

    if mode == 'HDF':
        temp_diff = raw_features.get('temp_diff', 0)
        rpm = raw_features.get('rotational_speed', 0)
        threshold = PHYSICAL_THRESHOLDS['HDF']['temp_diff_threshold']

        if temp_diff < threshold:
            return (
                f"Heat dissipation failure risk ({prob_pct}% probability). "
                f"Cooling gap narrowed to {temp_diff:.1f}K "
                f"(critical threshold: {threshold}K). "
                f"Check cooling system and airflow."
            )
        else:
            return (
                f"Heat dissipation pattern detected ({prob_pct}% probability). "
                f"Temperature differential approaching critical range."
            )

    elif mode == 'PWF':
        power = raw_features.get('power', 0)
        p_min = PHYSICAL_THRESHOLDS['PWF']['power_min']
        p_max = PHYSICAL_THRESHOLDS['PWF']['power_max']

        if power < p_min:
            return (
                f"Power failure risk — undervoltage ({prob_pct}% probability). "
                f"Power draw: {power:.0f}W (minimum: {p_min}W). "
                f"Inspect motor and power supply."
            )
        elif power > p_max:
            return (
                f"Power failure risk — overload ({prob_pct}% probability). "
                f"Power draw: {power:.0f}W (maximum: {p_max}W). "
                f"Check for mechanical obstruction."
            )
        else:
            return (
                f"Power consumption flagged ({prob_pct}% probability). "
                f"Current power: {power:.0f}W. Monitor motor current."
            )

    elif mode == 'OSF':
        tool_wear_torque = raw_features.get('tool_wear_torque', 0)
        return (
            f"Overstrain failure risk ({prob_pct}% probability). "
            f"Wear-torque load: {tool_wear_torque:.0f} exceeds safe limits. "
            f"Reduce feed rate or replace tool immediately."
        )

    elif mode == 'TWF':
        # Key is 'tool_wear' to match your CSV column name
        tool_wear = raw_features.get('tool_wear', 0)
        threshold = PHYSICAL_THRESHOLDS['TWF']['tool_wear_threshold']
        return (
            f"Tool wear failure risk ({prob_pct}% probability). "
            f"Current wear: {tool_wear:.0f} min "
            f"(replacement threshold: {threshold} min). "
            f"Schedule tool replacement."
        )

    return ''


def _generate_action(active_modes: list, failure_prob: float, raw_features: dict) -> str:
    if failure_prob >= 0.90:
        return "CRITICAL: Stop machine immediately. Contact maintenance supervisor."
    if 'HDF' in active_modes:
        return "Check cooling system and ventilation. Inspect heat exchangers."
    if 'TWF' in active_modes:
        tool_wear = raw_features.get('tool_wear', 0)
        return f"Replace tool immediately. Current wear: {tool_wear:.0f} min."
    if 'OSF' in active_modes:
        return "Reduce machine load. Inspect bearings and mechanical components."
    if 'PWF' in active_modes:
        return "Inspect electrical connections, motor windings, and power supply."
    return "Increase monitoring frequency. Schedule preventive inspection."