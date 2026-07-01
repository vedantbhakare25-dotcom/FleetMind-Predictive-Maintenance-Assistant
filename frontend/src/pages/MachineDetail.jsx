// Machine Detail page — the "money screen" of FleetMind
// Shows health score, failure risk, SHAP explanation, RUL, and root cause

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Clock, AlertTriangle, RefreshCw, Zap } from 'lucide-react'
import api from '../lib/api'
import HealthGauge from '../components/HealthGauge'
import SHAPBarChart from '../components/SHAPBarChart'
import StatusBadge from '../components/StatusBadge'

function MachineDetail() {
  const { machineId } = useParams()
  const navigate = useNavigate()

  const [machine, setMachine] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [loading, setLoading] = useState(true)
  const [predicting, setPredicting] = useState(false)
  const [error, setError] = useState('')

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const [machineRes, predictionRes] = await Promise.all([
        api.get(`/api/machines/${machineId}`),
        api.get(`/api/predictions/${machineId}/latest`)
      ])

      setMachine(machineRes.data)

      // /latest returns { message: "..." } if no predictions exist yet
      if (predictionRes.data.message) {
        setPrediction(null)
      } else {
        setPrediction(predictionRes.data)
      }
    } catch (err) {
      setError('Failed to load machine data.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const runNewPrediction = async () => {
    setPredicting(true)
    try {
      const res = await api.post(`/api/predictions/run/${machineId}`)
      setPrediction(res.data)
    } catch (err) {
      setError('Prediction failed. Make sure sensor data exists for this machine.')
      console.error(err)
    } finally {
      setPredicting(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [machineId])

  if (loading) {
    return <div className="p-8 text-slate-500">Loading machine details...</div>
  }

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Top bar */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-slate-500 hover:text-slate-700"
          >
            <ArrowLeft size={18} />
            Back to Dashboard
          </button>
          <button
            onClick={runNewPrediction}
            disabled={predicting}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2
                       rounded-lg text-sm font-medium hover:bg-blue-700
                       disabled:opacity-50 transition"
          >
            {predicting ? (
              <RefreshCw size={16} className="animate-spin" />
            ) : (
              <Zap size={16} />
            )}
            {predicting ? 'Running...' : 'Run New Prediction'}
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-6">

        {error && (
          <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Machine name + type */}
        {machine && (
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-slate-900">{machine.name}</h1>
            <p className="text-slate-500">
              {machine.machine_type} · {machine.location || 'No location set'}
            </p>
          </div>
        )}

        {/* No predictions yet */}
        {!prediction && (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
            <AlertTriangle className="mx-auto text-slate-400 mb-3" size={32} />
            <p className="text-slate-600 mb-1">No predictions yet for this machine.</p>
            <p className="text-sm text-slate-400">
              Click "Run New Prediction" above, or send sensor data first
              via the simulation script.
            </p>
          </div>
        )}

        {/* Prediction exists — show everything */}
        {prediction && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

            {/* Left column: Health gauge + RUL */}
            <div className="md:col-span-1 space-y-6">
              <div className="bg-white rounded-xl border border-slate-200 p-6
                              flex flex-col items-center">
                <HealthGauge
                  score={prediction.health_score.score}
                  level={prediction.health_score.level}
                />
                <p className="text-xs text-slate-500 mt-4 text-center">
                  {prediction.health_score.recommendation}
                </p>
              </div>

              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <div className="flex items-center gap-2 text-slate-500 text-sm mb-2">
                  <Clock size={16} />
                  Remaining Useful Life
                </div>
                <p className="text-2xl font-bold text-slate-900">
                  {prediction.rul.cycles_remaining} cycles
                </p>
                <p className="text-sm text-slate-400">
                  ≈ {prediction.rul.hours_remaining} hours · {prediction.rul.trend}
                </p>
              </div>

              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <p className="text-sm text-slate-500 mb-1">Failure Probability</p>
                <p className="text-2xl font-bold text-slate-900">
                  {(prediction.failure_probability * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-slate-400">
                  Confidence: {prediction.confidence}
                </p>
              </div>
            </div>

            {/* Right column: SHAP + Root Cause */}
            <div className="md:col-span-2 space-y-6">

              {/* SHAP Explainability */}
              <div className="bg-white rounded-xl border border-slate-200 p-6">
                <h2 className="font-semibold text-slate-900 mb-4">
                  Why is this machine at risk?
                </h2>
                <SHAPBarChart topFactors={prediction.explainability.top_factors} />
              </div>

              {/* Root Cause */}
              <div className="bg-white rounded-xl border border-slate-200 p-6">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="font-semibold text-slate-900">Root Cause Analysis</h2>
                  <StatusBadge level={prediction.alert_level} />
                </div>

                <p className="font-medium text-slate-800 mb-2">
                  {prediction.root_cause.primary_cause}
                </p>
                <p className="text-sm text-slate-600 mb-4">
                  {prediction.root_cause.detailed_text}
                </p>

                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                  <p className="text-xs text-slate-500 mb-1">Recommended Action</p>
                  <p className="text-sm font-medium text-slate-800">
                    {prediction.root_cause.action_required}
                  </p>
                </div>

                {prediction.root_cause.active_modes.length > 0 && (
                  <div className="flex gap-2 mt-4">
                    {prediction.root_cause.active_modes.map((mode) => (
                      <span
                        key={mode}
                        className="text-xs font-medium px-2 py-1 bg-slate-100
                                   text-slate-600 rounded-md"
                      >
                        {mode}
                      </span>
                    ))}
                  </div>
                )}
              </div>

            </div>
          </div>
        )}

      </main>
    </div>
  )
}

export default MachineDetail