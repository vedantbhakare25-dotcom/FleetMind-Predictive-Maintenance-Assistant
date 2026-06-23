// Color-coded badge for alert levels — used across Dashboard, Detail, Alerts

const LEVEL_STYLES = {
  CRITICAL : 'bg-red-100 text-red-700 border-red-200',
  HIGH     : 'bg-orange-100 text-orange-700 border-orange-200',
  MEDIUM   : 'bg-yellow-100 text-yellow-700 border-yellow-200',
  LOW      : 'bg-blue-100 text-blue-700 border-blue-200',
  NORMAL   : 'bg-green-100 text-green-700 border-green-200',
  UNKNOWN  : 'bg-slate-100 text-slate-600 border-slate-200'
}

function StatusBadge({ level }) {
  const style = LEVEL_STYLES[level] || LEVEL_STYLES.UNKNOWN

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full
                       text-xs font-medium border ${style}`}>
      {level || 'UNKNOWN'}
    </span>
  )
}

export default StatusBadge