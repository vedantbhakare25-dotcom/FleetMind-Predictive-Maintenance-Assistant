// SHAP explainability bars — shows why the model made this prediction

function SHAPBarChart({ topFactors }) {
  if (!topFactors || topFactors.length === 0) {
    return <p className="text-sm text-slate-400">No explanation available.</p>
  }

  const maxPercentage = Math.max(...topFactors.map(f => f.percentage))

  return (
    <div className="space-y-3">
      {topFactors.map((factor, idx) => {
        const isRisk = factor.direction === 'RISK'
        const barColor = isRisk ? 'bg-red-500' : 'bg-green-500'
        const textColor = isRisk ? 'text-red-600' : 'text-green-600'
        const widthPct = (factor.percentage / maxPercentage) * 100

        return (
          <div key={idx}>
            <div className="flex justify-between items-baseline mb-1">
              <span className="text-sm font-medium text-slate-700">
                {factor.feature}
              </span>
              <span className={`text-sm font-semibold ${textColor}`}>
                {isRisk ? '+' : '−'}{factor.percentage.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2.5">
              <div
                className={`h-2.5 rounded-full ${barColor}`}
                style={{ width: `${widthPct}%`, transition: 'width 0.4s ease' }}
              />
            </div>
          </div>
        )
      })}
      <p className="text-xs text-slate-400 mt-3">
        Red bars increase failure risk. Green bars reduce it.
      </p>
    </div>
  )
}

export default SHAPBarChart