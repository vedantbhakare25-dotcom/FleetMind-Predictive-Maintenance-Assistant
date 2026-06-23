// Single machine card on the Dashboard grid
// Shows health score, alert level, and key stats at a glance

import { useNavigate } from 'react-router-dom'
import { Activity, Clock } from 'lucide-react'
import StatusBadge from './StatusBadge'

const HEALTH_COLOR = (score) => {
  if (score === null || score === undefined) return 'text-slate-400'
  if (score <= 20) return 'text-red-600'
  if (score <= 40) return 'text-orange-600'
  if (score <= 60) return 'text-yellow-600'
  if (score <= 75) return 'text-blue-600'
  return 'text-green-600'
}

function MachineCard({ machine }) {
  const navigate = useNavigate()

  const healthScore = machine.health_score
  const hasData = healthScore !== null && healthScore !== undefined

  return (
    <div
      onClick={() => navigate(`/machines/${machine.id}`)}
      className="bg-white rounded-xl border border-slate-200 p-5 cursor-pointer
                 hover:shadow-md hover:border-slate-300 transition"
    >
      {/* Header: name + status badge */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-slate-900">{machine.name}</h3>
          <p className="text-xs text-slate-500">{machine.machine_type}</p>
        </div>
        <StatusBadge level={machine.alert_level} />
      </div>

      {/* Health score */}
      <div className="flex items-baseline gap-1 mb-3">
        <span className={`text-3xl font-bold ${HEALTH_COLOR(healthScore)}`}>
          {hasData ? healthScore.toFixed(0) : '—'}
        </span>
        <span className="text-sm text-slate-400">/100</span>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4 text-xs text-slate-500">
        {hasData && (
          <div className="flex items-center gap-1">
            <Activity size={14} />
            {(machine.failure_probability * 100).toFixed(0)}% risk
          </div>
        )}
        {machine.rul_cycles !== null && machine.rul_cycles !== undefined && (
          <div className="flex items-center gap-1">
            <Clock size={14} />
            {machine.rul_cycles} cycles left
          </div>
        )}
        {!hasData && (
          <span className="text-slate-400">No predictions yet</span>
        )}
      </div>
    </div>
  )
}

export default MachineCard