// Single alert card for the Alert Center
// Shows severity, machine, message, and acknowledge action

import { useState } from 'react'
import { AlertTriangle, CheckCircle, Clock } from 'lucide-react'
import StatusBadge from './StatusBadge'

const LEVEL_BORDER = {
  CRITICAL : 'border-l-red-500',
  HIGH     : 'border-l-orange-500',
  MEDIUM   : 'border-l-yellow-500',
  LOW      : 'border-l-blue-500'
}

function AlertBanner({ alert, onAcknowledge }) {
  const [acknowledging, setAcknowledging] = useState(false)
  const [note, setNote] = useState('')
  const [showNoteInput, setShowNoteInput] = useState(false)

  const machineName = alert.machines?.name || 'Unknown Machine'
  const machineType = alert.machines?.machine_type || ''
  const borderColor = LEVEL_BORDER[alert.level] || 'border-l-slate-300'

  const handleAcknowledge = async () => {
    setAcknowledging(true)
    try {
      await onAcknowledge(alert.id, note)
    } finally {
      setAcknowledging(false)
    }
  }

  const timeAgo = (dateStr) => {
    const diffMs = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diffMs / 60000)
    if (mins < 1) return 'just now'
    if (mins < 60) return `${mins}m ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours}h ago`
    return `${Math.floor(hours / 24)}d ago`
  }

  return (
    <div className={`bg-white rounded-xl border border-slate-200 border-l-4
                      ${borderColor} p-5`}>

      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <AlertTriangle size={18} className="text-slate-400" />
          <div>
            <p className="font-semibold text-slate-900">{machineName}</p>
            <p className="text-xs text-slate-400">{machineType}</p>
          </div>
        </div>
        <StatusBadge level={alert.level} />
      </div>

      {/* Message */}
      <p className="text-sm font-medium text-slate-800 mb-1">{alert.title}</p>
      <p className="text-sm text-slate-600 mb-3">{alert.message}</p>

      {alert.root_cause && (
        <p className="text-xs text-slate-500 bg-slate-50 rounded-lg p-2 mb-3">
          {alert.root_cause}
        </p>
      )}

      {/* Footer: time + acknowledge */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-100">
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <Clock size={14} />
          {timeAgo(alert.created_at)}
        </div>

        {!showNoteInput ? (
          <button
            onClick={() => setShowNoteInput(true)}
            className="flex items-center gap-1 text-sm font-medium text-blue-600
                       hover:text-blue-700"
          >
            <CheckCircle size={16} />
            Acknowledge
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Add a note (optional)"
              className="text-xs border border-slate-200 rounded-lg px-2 py-1
                         focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button
              onClick={handleAcknowledge}
              disabled={acknowledging}
              className="text-xs font-medium bg-blue-600 text-white px-3 py-1.5
                         rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {acknowledging ? '...' : 'Confirm'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default AlertBanner