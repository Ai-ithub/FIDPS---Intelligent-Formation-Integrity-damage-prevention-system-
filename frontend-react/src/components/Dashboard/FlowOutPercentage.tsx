import { Activity } from 'lucide-react'

interface FlowOutPercentageProps {
  flowIn?: number // Flow In (gpm)
  flowOut?: number // Flow Out (gpm)
  warningThreshold?: number // Warning threshold for difference
  dangerThreshold?: number // Danger threshold for difference
}

const FlowOutPercentage = ({
  flowIn = 1000,
  flowOut = 995,
  warningThreshold = 5,
  dangerThreshold = 10,
}: FlowOutPercentageProps) => {
  const percentage = flowIn > 0 ? (flowOut / flowIn) * 100 : 0

  // Determine status
  const getStatus = () => {
    if (percentage < 95) {
      return {
        status: 'danger',
        color: 'red',
        label: 'Lost Circulation - Critical Flow Loss',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-500',
        message: '⚠️ Critical: Significant flow loss detected (Lost Circulation) - Drilling fluid is being lost into the formation, requiring immediate attention',
      }
    } else if (percentage > 105) {
      return {
        status: 'danger',
        color: 'red',
        label: 'Kick - Formation Fluid Influx',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-500',
        message: '❌ Critical: Formation fluid influx detected - Formation fluid is entering the wellbore (Kick)',
      }
    } else if (percentage < 98 || percentage > 102) {
      return {
        status: 'warning',
        color: 'yellow',
        label: 'Flow Deviation from Target',
        bgColor: 'bg-yellow-50',
        borderColor: 'border-yellow-500',
        message: '⚠️ Warning: Flow rate deviation from target 100%',
      }
    } else {
      return {
        status: 'safe',
        color: 'green',
        label: 'Normal Flow',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-500',
        message: '✅ All systems normal',
      }
    }
  }

  const status = getStatus()
  const difference = flowOut - flowIn

  return (
    <div className={`card p-6 ${status.bgColor} border-l-4 ${status.borderColor}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <Activity className="mr-2 h-5 w-5" />
          Flow Out Percentage
        </h3>
        <span className={`status-badge status-${status.status}`}>
          {status.label}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Percentage Display */}
        <div className="flex flex-col items-center justify-center">
          <div className="relative w-40 h-40 mb-4">
            <svg width="160" height="160" viewBox="0 0 160 160" className="transform -rotate-90">
              {/* Background circle */}
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="12"
              />
              {/* Progress circle */}
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke={status.color === 'red' ? '#ef4444' : status.color === 'yellow' ? '#eab308' : '#22c55e'}
                strokeWidth="12"
                strokeDasharray={`${(percentage / 100) * 439.8} 439.8`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div
                  className="text-4xl font-bold"
                  style={{
                    color: status.color === 'red' ? '#ef4444' : status.color === 'yellow' ? '#eab308' : '#22c55e',
                  }}
                >
                  {percentage.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600 mt-1">Flow Out</div>
              </div>
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-600">Target Percentage: 100%</div>
          </div>
        </div>

        {/* Flow Values */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Flow In</div>
            <div className="text-3xl font-bold text-blue-600">{flowIn.toFixed(1)}</div>
            <div className="text-sm text-gray-500 mt-1">gpm</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Flow Out</div>
            <div className="text-3xl font-bold text-green-600">{flowOut.toFixed(1)}</div>
            <div className="text-sm text-gray-500 mt-1">gpm</div>
          </div>

          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Difference</div>
            <div className={`text-2xl font-bold ${difference > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {difference > 0 ? '+' : ''}{difference.toFixed(1)} gpm
            </div>
          </div>
        </div>

        {/* Status and Warnings */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm font-semibold text-gray-700 mb-2">Formula:</div>
            <div className="text-sm font-mono bg-gray-50 p-2 rounded">
              (Flow Out / Flow In) × 100
            </div>
          </div>

          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm font-semibold text-gray-700 mb-2">Alert Thresholds:</div>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span>✅ Safe:</span>
                <span className="font-bold">98% - 102%</span>
              </div>
              <div className="flex items-center justify-between">
                <span>⚠️ Warning:</span>
                <span className="font-bold">95% - 98% or 102% - 105%</span>
              </div>
              <div className="flex items-center justify-between">
                <span>❌ Lost Circulation:</span>
                <span className="font-bold">&lt; 95%</span>
              </div>
              <div className="flex items-center justify-between">
                <span>❌ Kick:</span>
                <span className="font-bold">&gt; 105%</span>
              </div>
            </div>
          </div>

          {status.message && (
            <div className={`p-3 rounded-lg text-sm font-medium ${status.status === 'danger' ? 'bg-red-100 text-red-800' : status.status === 'warning' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
              {status.message}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default FlowOutPercentage

