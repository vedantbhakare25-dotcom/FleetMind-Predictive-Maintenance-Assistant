// Alert Center — lists all active alerts across the plant
// Ramesh reviews and acknowledges them here

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Inbox, RefreshCw } from 'lucide-react'
import api from '../lib/api'
import AlertBanner from '../components/AlertBanner'

function AlertCenter() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const navigate = useNavigate()

  const fetchAlerts = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get('/api/alerts')
      setAlerts(response.data || [])
    } catch (err) {
      setError('Failed to load alerts.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleAcknowledge = async (alertId, note) => {
    try {
      await api.patch(`/api/alerts/${alertId}/acknowledge`, { note: note || null })
      // Remove acknowledged alert from the active list immediately
      setAlerts((prev) => prev.filter((a) => a.id !== alertId))
    } catch (err) {
      console.error('Failed to acknowledge alert:', err)
      alert('Failed to acknowledge alert. Please try again.')
    }
  }

  useEffect(() => {
    fetchAlerts()
  }, [])

  // Sort: CRITICAL first, then HIGH, MEDIUM, LOW
  const levelOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 }
  const sortedAlerts = [...alerts].sort(
    (a, b) => (levelOrder[a.level] ?? 9) - (levelOrder[b.level] ?? 9)
  )

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Top bar */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-slate-500 hover:text-slate-700"
          >
            <ArrowLeft size={18} />
            Back to Dashboard
          </button>
          <button
            onClick={fetchAlerts}
            className="p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition"
          >
            <RefreshCw size={18} />
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto p-6">

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">
            Active Alerts {alerts.length > 0 && `(${alerts.length})`}
          </h1>
          <p className="text-slate-500 text-sm">
            Review and acknowledge alerts across your plant
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {loading && (
          <p className="text-slate-500 text-center py-12">Loading alerts...</p>
        )}

        {!loading && sortedAlerts.length === 0 && !error && (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <Inbox className="mx-auto text-slate-300 mb-3" size={32} />
            <p className="text-slate-600">No active alerts.</p>
            <p className="text-sm text-slate-400">All machines operating normally.</p>
          </div>
        )}

        <div className="space-y-4">
          {sortedAlerts.map((alert) => (
            <AlertBanner
              key={alert.id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
            />
          ))}
        </div>

      </main>
    </div>
  )
}

export default AlertCenter