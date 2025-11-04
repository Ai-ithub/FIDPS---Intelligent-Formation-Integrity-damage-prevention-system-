
interface DeltaPGaugeProps {
  value: number
  min: number
  max: number
  optimalRange: { min: number; max: number }
}

const DeltaPGauge = ({ value, min, max, optimalRange }: DeltaPGaugeProps) => {
  const getStatus = () => {
    if (value < 0) return { color: 'red', label: 'Underbalance - Kick Risk', severity: 'critical' }
    if (value < optimalRange.min) return { color: 'yellow', label: 'Low Overbalance', severity: 'warning' }
    if (value > optimalRange.max) return { color: 'orange', label: 'High Overbalance - Damage Risk', severity: 'warning' }
    if (value > max * 0.8) return { color: 'red', label: 'Critical Overbalance', severity: 'critical' }
    return { color: 'green', label: 'Optimal', severity: 'normal' }
  }

  const status = getStatus()
  const percentage = ((value - min) / (max - min)) * 100

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-white rounded-lg shadow-md">
      <h3 className="text-lg font-semibold mb-4">Differential Pressure (ΔP)</h3>
      <div className="relative w-64 h-64">
        <svg viewBox="0 0 200 200" className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="20"
          />
          {/* Optimal range */}
          <circle
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke="#10b981"
            strokeWidth="20"
            strokeDasharray={`${((optimalRange.max - optimalRange.min) / (max - min)) * 502.4} 502.4`}
            strokeDashoffset={((min - optimalRange.min) / (max - min)) * 502.4}
            opacity="0.3"
          />
          {/* Value arc */}
          <circle
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke={status.color === 'green' ? '#10b981' : status.color === 'yellow' ? '#f59e0b' : '#ef4444'}
            strokeWidth="20"
            strokeDasharray={`${(percentage / 100) * 502.4} 502.4`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className={`text-4xl font-bold ${status.color === 'green' ? 'text-green-600' : status.color === 'yellow' ? 'text-yellow-600' : 'text-red-600'}`}>
            {value.toFixed(0)}
          </div>
          <div className="text-sm text-gray-500 mt-1">psi</div>
          <div className={`text-xs mt-2 px-2 py-1 rounded ${status.severity === 'critical' ? 'bg-red-100 text-red-800' : status.severity === 'warning' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
            {status.label}
          </div>
        </div>
      </div>
      <div className="mt-4 text-sm text-gray-600">
        <div>Safe Range: {optimalRange.min} - {optimalRange.max} psi</div>
        <div>Current: {value.toFixed(1)} psi</div>
      </div>
    </div>
  )
}

export default DeltaPGauge

