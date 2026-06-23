// Dashboard — main landing page after login
// Fetches GET /api/machines and renders summary + machine grid

import { useState, useEffect } from 'react'
import { LogOut, RefreshCw } from 'lucide-react'
import api from '../lib/api'
import { useAuth } from '../context/AuthContext'
import MachineCard from '../components/MachineCard'

function SummaryCard({ label, count, color }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 px-4 py-3 flex-1">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{count}</p>
    </div>
  )
}

function Dashboard() {
  const [machines, setMachines] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const { user, signOut } = useAuth()

  const fetchMachines = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get('/api/machines')
      setMachines(response.data.machines || [])
      setSummary(response.data.summary || null)
    } catch (err) {
      setError('Failed to load machines. Is the backend running?')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMachines()
  }, [])

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Top bar */}
      <header className="bg-white border-b border-slate-200 px-6 py-4
                          flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-900">FleetMind</h1>
          <p className="text-xs text-slate-500">{user?.email}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchMachines}
            className="p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCw size={18} />
          </button>
          <button
            onClick={signOut}
            className="flex items-center gap-1 text-sm text-slate-500
                       hover:bg-slate-100 px-3 py-2 rounded-lg transition"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </header>

      <main className="p-6 max-w-6xl mx-auto">

        {/* Error state */}
        {error && (
          <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Summary cards */}
        {summary && (
          <div className="flex gap-3 mb-6">
            <SummaryCard label="Total Machines" count={summary.total_machines} color="text-slate-900" />
            <SummaryCard label="Critical" count={summary.critical_count} color="text-red-600" />
            <SummaryCard label="High" count={summary.high_count} color="text-orange-600" />
            <SummaryCard label="Medium" count={summary.medium_count} color="text-yellow-600" />
            <SummaryCard label="Normal" count={summary.normal_count} color="text-green-600" />
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <p className="text-slate-500 text-center py-12">Loading machines...</p>
        )}

        {/* Machine grid */}
        {!loading && machines.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {machines.map((machine) => (
              <MachineCard key={machine.id} machine={machine} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && machines.length === 0 && !error && (
          <p className="text-slate-500 text-center py-12">
            No machines found for your plant.
          </p>
        )}

      </main>
    </div>
  )
}

export default Dashboard