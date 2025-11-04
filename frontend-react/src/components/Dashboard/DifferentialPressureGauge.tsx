import { Gauge } from 'lucide-react'

interface DifferentialPressureGaugeProps {
  deltaP?: number // ΔP = ECD - Pore Pressure (psi)
  ecd?: number // Current ECD (ppg)
  porePressure?: number // Pore Pressure (ppg)
  warningThreshold?: number // Warning threshold (default 150 psi)
  dangerThreshold?: number // Danger threshold (default 200 psi)
}

const DifferentialPressureGauge = ({
  deltaP = 120,
  ecd = 10.2,
  porePressure = 9.5,
  warningThreshold = 150,
  dangerThreshold = 200,
}: DifferentialPressureGaugeProps) => {
  // Calculate percentage for gauge display (assuming range from -50 to 250 psi)
  const minValue = -50
  const maxValue = 250
  const percentage = ((deltaP - minValue) / (maxValue - minValue)) * 100
  const clampedPercentage = Math.max(0, Math.min(100, percentage))

  // Determine status
  const getStatus = () => {
    if (deltaP < 0) {
      return { status: 'danger', color: 'red', label: 'Underbalance - Kick Risk', bgColor: 'bg-red-50', borderColor: 'border-red-500' }
    } else if (deltaP > dangerThreshold) {
      return { status: 'danger', color: 'red', label: 'High Overbalance - Mechanical Damage Risk', bgColor: 'bg-red-50', borderColor: 'border-red-500' }
    } else if (deltaP > warningThreshold) {
      return { status: 'warning', color: 'yellow', label: 'Elevated Overbalance - Monitor', bgColor: 'bg-yellow-50', borderColor: 'border-yellow-500' }
    } else {
      return { status: 'safe', color: 'green', label: 'Safe Zone', bgColor: 'bg-green-50', borderColor: 'border-green-500' }
    }
  }

  const status = getStatus()

  // Gauge visualization using SVG
  const gaugeAngle = (clampedPercentage / 100) * 180 - 90 // Convert to -90 to 90 degrees

  return (
    <div className={`card p-6 ${status.bgColor} border-l-4 ${status.borderColor}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <Gauge className="mr-2 h-5 w-5" />
          Differential Pressure Gauge (ΔP)
        </h3>
        <span className={`status-badge status-${status.status}`}>
          {status.label}
        </span>
      </div>

      <div className="flex items-center justify-center space-x-8">
        {/* Gauge Visualization */}
        <div className="relative w-48 h-48">
          <svg width="200" height="120" viewBox="0 0 200 120" className="w-full h-full">
            {/* Background arc */}
            <path
              d="M 20 100 A 80 80 0 0 1 180 100"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="20"
            />
            {/* Safe zone (green) */}
            <path
              d="M 20 100 A 80 80 0 0 1 100 20"
              fill="none"
              stroke="#22c55e"
              strokeWidth="20"
            />
            {/* Warning zone (yellow) */}
            <path
              d="M 100 20 A 80 80 0 0 1 160 60"
              fill="none"
              stroke="#eab308"
              strokeWidth="20"
            />
            {/* Danger zone (red) */}
            <path
              d="M 160 60 A 80 80 0 0 1 180 100"
              fill="none"
              stroke="#ef4444"
              strokeWidth="20"
            />
            {/* Needle */}
            <line
              x1="100"
              y1="100"
              x2={100 + 70 * Math.cos((gaugeAngle * Math.PI) / 180)}
              y2={100 - 70 * Math.sin((gaugeAngle * Math.PI) / 180)}
              stroke={status.color === 'red' ? '#ef4444' : status.color === 'yellow' ? '#eab308' : '#22c55e'}
              strokeWidth="4"
              strokeLinecap="round"
            />
            {/* Center circle */}
            <circle cx="100" cy="100" r="8" fill={status.color === 'red' ? '#ef4444' : status.color === 'yellow' ? '#eab308' : '#22c55e'} />
          </svg>
          {/* Value display */}
          <div className="absolute top-16 left-1/2 transform -translate-x-1/2 text-center">
            <div className="text-3xl font-bold" style={{ color: status.color === 'red' ? '#ef4444' : status.color === 'yellow' ? '#eab308' : '#22c55e' }}>
              {deltaP.toFixed(1)}
            </div>
            <div className="text-sm text-gray-600">psi</div>
          </div>
        </div>

        {/* Information Panel */}
        <div className="flex-1 space-y-3">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Calculation Formula:</div>
            <div className="text-lg font-mono">
              ΔP = ECD - Pore Pressure
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-lg p-3 border border-gray-200">
              <div className="text-xs text-gray-600 mb-1">Current ECD</div>
              <div className="text-xl font-bold">{ecd.toFixed(2)} ppg</div>
            </div>
            <div className="bg-white rounded-lg p-3 border border-gray-200">
              <div className="text-xs text-gray-600 mb-1">Pore Pressure</div>
              <div className="text-xl font-bold">{porePressure.toFixed(2)} ppg</div>
            </div>
          </div>

          <div className="bg-white rounded-lg p-3 border border-gray-200">
            <div className="text-xs text-gray-600 mb-2">Alert Thresholds:</div>
            <div className="space-y-1 text-sm">
              <div className="flex items-center justify-between">
                <span>⚠️ Warning (Yellow):</span>
                <span className="font-bold">&gt; {warningThreshold} psi</span>
              </div>
              <div className="flex items-center justify-between">
                <span>🚨 Danger (Red):</span>
                <span className="font-bold">&gt; {dangerThreshold} psi</span>
              </div>
              <div className="flex items-center justify-between">
                <span>⚠️ Underbalance:</span>
                <span className="font-bold">&lt; 0 psi</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DifferentialPressureGauge
