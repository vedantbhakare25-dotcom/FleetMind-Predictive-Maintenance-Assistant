// Circular health score gauge — the centerpiece of the Machine Detail page

const LEVEL_COLOR = {
  CRITICAL : '#dc2626',
  HIGH     : '#ea580c',
  MEDIUM   : '#ca8a04',
  LOW      : '#2563eb',
  NORMAL   : '#16a34a'
}

function HealthGauge({ score, level }) {
  const color = LEVEL_COLOR[level] || '#94a3b8'

  // SVG circle math: circumference = 2 * PI * radius
  const radius = 70
  const circumference = 2 * Math.PI * radius
  const progress = (score / 100) * circumference
  const dashOffset = circumference - progress

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-44 h-44">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 160 160">
          {/* Background track */}
          <circle
            cx="80" cy="80" r={radius}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth="12"
          />
          {/* Progress arc */}
          <circle
            cx="80" cy="80" r={radius}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.5s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold" style={{ color }}>
            {score.toFixed(0)}
          </span>
          <span className="text-xs text-slate-400">/ 100</span>
        </div>
      </div>
      <span
        className="mt-3 px-3 py-1 rounded-full text-sm font-semibold"
        style={{ color, backgroundColor: `${color}1A` }}
      >
        {level}
      </span>
    </div>
  )
}

export default HealthGauge