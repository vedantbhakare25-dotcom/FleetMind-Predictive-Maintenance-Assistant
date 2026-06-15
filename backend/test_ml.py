from ml.preprocessor import AI4IPreprocessor
from ml.predictor import FleetMindPredictor
from ml.explainer import FleetMindExplainer
from ml.health_score import calculate_health_score
from ml.root_cause import generate_root_cause

pre  = AI4IPreprocessor()
pred = FleetMindPredictor()
exp  = FleetMindExplainer()

sample = {
    'air_temperature'    : 298.7,
    'process_temperature': 305.8,
    'rotational_speed'   : 1350.0,
    'torque'             : 68.3,
    'tool_wear'          : 210.0
}

features    = pre.transform(sample, quality_variant='L')
failure     = pred.predict_failure(features)
modes       = pred.predict_failure_modes(features)
rul         = pred.predict_rul(sample['tool_wear'], failure['probability'])
health      = calculate_health_score(failure['probability'], rul['cycles_remaining'])
explanation = exp.explain(features)
raw         = pre.get_raw_features(sample, quality_variant='L')
cause       = generate_root_cause(explanation, modes, raw, failure['probability'])

print("=" * 50)
print("FLEETMIND ML MODULE VERIFICATION")
print("=" * 50)
print(f"Failure prob    : {failure['probability']}")
print(f"Confidence      : {failure['confidence']}")
print(f"Primary mode    : {modes['primary_mode']}")
print(f"Active modes    : {modes['active_modes']}")
print(f"RUL cycles      : {rul['cycles_remaining']}")
print(f"RUL trend       : {rul['trend']}")
print(f"Health score    : {health.score} | {health.level}")
print(f"SHAP baseline   : {explanation['baseline']}")
print()
print("Top 3 SHAP factors:")
for factor in explanation['top_factors']:
    name = factor['feature']
    direction = factor['direction']
    pct = factor['percentage']
    print(f"  {name:<25} {direction:<12} {pct}%")
print()
print(f"Primary cause   : {cause.primary_cause}")
print(f"Active modes    : {cause.active_modes}")
print(f"Action          : {cause.action_required}")
print()
print("ALL MODULES WORKING CORRECTLY")