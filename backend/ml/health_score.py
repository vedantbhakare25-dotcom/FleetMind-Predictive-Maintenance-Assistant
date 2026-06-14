# Calculates health score 0–100 from failure probability and normalized RUL using weighted formula (0.6 failure component + 0.4 RUL component), maps score to alert level (NORMAL, LOW, MEDIUM, HIGH, CRITICAL)
# Health score calculation and alert level mapping for FleetMind
# Translates ML probability outputs into human-readable scores

from dataclasses import dataclass


# ── Alert Level Thresholds ─────────────────────────────────────────────────────
# These match the values in .env / config.py
# Defined here as module constants for use without FastAPI context (notebooks, tests)

HEALTH_THRESHOLDS = {
    'CRITICAL' : 20.0,
    'HIGH'     : 40.0,
    'MEDIUM'   : 60.0,
    'LOW'      : 75.0,
    'NORMAL'   : 100.0
}

# Weights for health score formula
FAILURE_PROB_WEIGHT = 0.6
RUL_WEIGHT = 0.4

# RUL normalization ceiling (matches training notebook)
RUL_MAX_CYCLES = 125


@dataclass
class HealthScoreResult:
    """
    Structured result from health score calculation.
    Using dataclass instead of plain dict gives:
    - Attribute access (result.score vs result['score'])
    - Type hints
    - Automatic __repr__ for debugging
    """
    score         : float   # 0.0 to 100.0
    level         : str     # NORMAL, LOW, MEDIUM, HIGH, CRITICAL
    failure_component : float   # contribution from failure probability
    rul_component     : float   # contribution from RUL
    is_critical   : bool    # convenience flag for alert logic
    recommendation: str     # one-line action recommendation


def calculate_health_score(
    failure_prob: float,
    rul_cycles: int,
    rul_max: int = RUL_MAX_CYCLES
) -> HealthScoreResult:
    """
    Calculates machine health score from ML model outputs.

    Args:
        failure_prob: float [0.0, 1.0] from predict_failure()
        rul_cycles: int [0, 125] from predict_rul()
        rul_max: maximum expected RUL for normalization

    Returns:
        HealthScoreResult with score, level, and recommendation
    """

    # ── Validate inputs ────────────────────────────────────────────────────────
    failure_prob = max(0.0, min(1.0, float(failure_prob)))
    rul_cycles = max(0, min(rul_max, int(rul_cycles)))


    # ── Component calculations ─────────────────────────────────────────────────

    # Failure component: inverse of failure probability, scaled to 100
    # failure_prob=0.0 → failure_component=100 (perfectly healthy)
    # failure_prob=1.0 → failure_component=0   (certain failure)
    failure_component = (1.0 - failure_prob) * 100

    # RUL component: normalized remaining life, scaled to 100
    # rul_cycles=125 → rul_component=100 (full life remaining)
    # rul_cycles=0   → rul_component=0   (no life remaining)
    rul_component = (rul_cycles / rul_max) * 100


    # ── Weighted combination ───────────────────────────────────────────────────
    raw_score = (
        FAILURE_PROB_WEIGHT * failure_component +
        RUL_WEIGHT * rul_component
    )

    # Round to 1 decimal place for display
    score = round(raw_score, 1)


    # ── Map score to alert level ───────────────────────────────────────────────
    level = _score_to_level(score)


    # ── Generate recommendation ────────────────────────────────────────────────
    recommendation = _level_to_recommendation(level, rul_cycles)


    return HealthScoreResult(
        score=score,
        level=level,
        failure_component=round(failure_component, 1),
        rul_component=round(rul_component, 1),
        is_critical=(level in ('CRITICAL', 'HIGH')),
        recommendation=recommendation
    )


def _score_to_level(score: float) -> str:
    """
    Maps health score to alert severity level.

    Note: thresholds are upper bounds for each level.
    score <= 20  → CRITICAL
    score <= 40  → HIGH
    score <= 60  → MEDIUM
    score <= 75  → LOW
    score > 75   → NORMAL
    """
    if score <= HEALTH_THRESHOLDS['CRITICAL']:
        return 'CRITICAL'
    elif score <= HEALTH_THRESHOLDS['HIGH']:
        return 'HIGH'
    elif score <= HEALTH_THRESHOLDS['MEDIUM']:
        return 'MEDIUM'
    elif score <= HEALTH_THRESHOLDS['LOW']:
        return 'LOW'
    else:
        return 'NORMAL'


def _level_to_recommendation(level: str, rul_cycles: int) -> str:
    """
    Returns a one-line maintenance recommendation
    based on alert level and remaining useful life.
    """
    recommendations = {
        'CRITICAL': f"IMMEDIATE ACTION REQUIRED — Stop machine and inspect. "
                    f"Estimated {rul_cycles} cycles remaining.",
        'HIGH'    : f"Schedule maintenance within 24 hours. "
                    f"Estimated {rul_cycles} cycles remaining.",
        'MEDIUM'  : f"Increase monitoring frequency. "
                    f"Plan maintenance within this week.",
        'LOW'     : "Monitor closely. No immediate action required.",
        'NORMAL'  : "Machine operating within normal parameters."
    }
    return recommendations.get(level, "Monitor machine status.")


def score_delta_trend(current_score: float, previous_score: float) -> dict:
    """
    Calculates how much the health score changed since last prediction.
    Used in the dashboard to show trend arrows (improving/declining).

    Args:
        current_score: latest health score
        previous_score: health score from previous prediction

    Returns:
        dict: {
            'delta': -14.3,
            'trend': 'DECLINING',
            'trend_symbol': '↓'
        }
    """
    delta = round(current_score - previous_score, 1)

    if delta > 2:
        trend, symbol = 'IMPROVING', '↑'
    elif delta < -2:
        trend, symbol = 'DECLINING', '↓'
    else:
        trend, symbol = 'STABLE', '→'

    return {
        'delta'        : delta,
        'trend'        : trend,
        'trend_symbol' : symbol
    }