import { AlertTriangle, AlertCircle, Info } from 'lucide-react'

interface Alert {
  id: string
  type: 'warning' | 'danger' | 'info'
  title: string
  message: string
  timestamp: string
}

interface IntelligentAlertsProps {
  deltaP?: number
  flowOutPercentage?: number
  torqueTrend?: 'increasing' | 'stable' | 'decreasing'
  hthpFluidLoss?: number
  hthpFluidLossThreshold?: number
}

const IntelligentAlerts = ({
  deltaP = 120,
  flowOutPercentage = 98,
  torqueTrend = 'stable',
  hthpFluidLoss = 12.5,
  hthpFluidLossThreshold = 20,
}: IntelligentAlertsProps) => {
  // Generate alerts based on current conditions
  const generateAlerts = (): Alert[] => {
    const alerts: Alert[] = []

    // Check differential pressure
    if (deltaP > 150 && deltaP <= 200) {
      alerts.push({
        id: '1',
        type: 'warning',
        title: 'Elevated Differential Pressure (ΔP)',
        message: 'Differential pressure is increasing. Risk of mechanical damage (particle invasion).',
        timestamp: new Date().toLocaleString(),
      })
    } else if (deltaP > 200) {
      alerts.push({
        id: '2',
        type: 'danger',
        title: 'High Differential Pressure (ΔP)',
        message: 'Differential pressure is critically high. High risk of mechanical damage.',
        timestamp: new Date().toLocaleString(),
      })
    } else if (deltaP < 0) {
      alerts.push({
        id: '3',
        type: 'danger',
        title: 'Underbalance Condition',
        message: 'Negative differential pressure detected. Risk of fluid influx (Kick).',
        timestamp: new Date().toLocaleString(),
      })
    }

    // Check flow out percentage
    if (flowOutPercentage < 95) {
      alerts.push({
        id: '4',
        type: 'danger',
        title: 'Lost Circulation Detected',
        message: 'Flow out percentage decreased! Possible formation fracture (Lost Circulation).',
        timestamp: new Date().toLocaleString(),
      })
    } else if (flowOutPercentage > 105) {
      alerts.push({
        id: '5',
        type: 'danger',
        title: 'Kick Condition',
        message: 'Flow out percentage increased! Formation may be returning fluid to well (Kick).',
        timestamp: new Date().toLocaleString(),
      })
    }

    // Check torque trend
    if (torqueTrend === 'increasing') {
      alerts.push({
        id: '6',
        type: 'warning',
        title: 'Increasing Torque',
        message: 'Torque is increasing. Possible shale swelling and chemical damage risk.',
        timestamp: new Date().toLocaleString(),
      })
    }

    // Check HTHP fluid loss
    if (hthpFluidLoss > hthpFluidLossThreshold) {
      alerts.push({
        id: '7',
        type: 'warning',
        title: 'HTHP Fluid Loss Out of Range',
        message: `Last HTHP Fluid Loss test (${hthpFluidLoss.toFixed(1)} ml/30min) is outside acceptable range. Risk of chemical damage.`,
        timestamp: new Date().toLocaleString(),
      })
    }

    return alerts.sort((a, b) => {
      const priority = { danger: 0, warning: 1, info: 2 }
      return priority[a.type] - priority[b.type]
    })
  }

  const alerts = generateAlerts()

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'danger':
        return <AlertTriangle className="h-5 w-5 text-red-600" />
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-600" />
      case 'info':
        return <Info className="h-5 w-5 text-blue-600" />
    }
  }

  const getAlertBgColor = (type: Alert['type']) => {
    switch (type) {
      case 'danger':
        return 'bg-red-50 border-red-200'
      case 'warning':
        return 'bg-yellow-50 border-yellow-200'
      case 'info':
        return 'bg-blue-50 border-blue-200'
    }
  }

  const getAlertTextColor = (type: Alert['type']) => {
    switch (type) {
      case 'danger':
        return 'text-red-800'
      case 'warning':
        return 'text-yellow-800'
      case 'info':
        return 'text-blue-800'
    }
  }

  if (alerts.length === 0) {
    return (
      <div className="card p-6">
        <div className="flex items-center mb-4">
          <AlertTriangle className="mr-2 h-6 w-6 text-green-600" />
          <h2 className="text-2xl font-bold text-gray-900">Intelligent Alerts</h2>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <div className="text-green-800 font-medium">
            ✅ All parameters are within safe operating ranges. No alerts at this time.
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="card p-6">
      <div className="flex items-center mb-4">
        <AlertTriangle className="mr-2 h-6 w-6 text-orange-600" />
        <h2 className="text-2xl font-bold text-gray-900">Intelligent Alerts</h2>
        <span className="ml-auto bg-orange-100 text-orange-800 text-sm font-semibold px-3 py-1 rounded-full">
          {alerts.length} Active Alert{alerts.length > 1 ? 's' : ''}
        </span>
      </div>

      <div className="space-y-4">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`rounded-lg border-l-4 p-4 ${getAlertBgColor(alert.type)} ${
              alert.type === 'danger' ? 'border-l-red-500' : alert.type === 'warning' ? 'border-l-yellow-500' : 'border-l-blue-500'
            }`}
          >
            <div className="flex items-start">
              <div className="flex-shrink-0 mr-3">{getAlertIcon(alert.type)}</div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <h3 className={`font-semibold ${getAlertTextColor(alert.type)}`}>{alert.title}</h3>
                  <span className={`text-xs ${getAlertTextColor(alert.type)} opacity-75`}>{alert.timestamp}</span>
                </div>
                <p className={`text-sm ${getAlertTextColor(alert.type)} opacity-90`}>{alert.message}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="text-xs text-gray-600">
          <strong>Note:</strong> This intelligent alert system analyzes real-time drilling parameters and provides contextual warnings based on formation damage risk indicators. Alerts are automatically generated when parameters exceed safe operating thresholds.
        </div>
      </div>
    </div>
  )
}

export default IntelligentAlerts
