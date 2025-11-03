import { AlertTriangle, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface Alert {
  id: string
  well_id: string
  timestamp: string
  anomaly_type: string
  severity: string
  description: string
}

interface RecentAlertsProps {
  alerts: Alert[]
}

const RecentAlerts = ({ alerts }: RecentAlertsProps) => {
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'border-l-red-500 bg-red-50'
      case 'warning':
        return 'border-l-yellow-500 bg-yellow-50'
      case 'info':
        return 'border-l-blue-500 bg-blue-50'
      default:
        return 'border-l-gray-500 bg-gray-50'
    }
  }

  const getSeverityBadge = (severity: string) => {
    const baseClass = 'px-2 py-1 rounded-full text-xs font-semibold'
    switch (severity.toLowerCase()) {
      case 'critical':
        return `${baseClass} bg-red-100 text-red-800`
      case 'warning':
        return `${baseClass} bg-yellow-100 text-yellow-800`
      case 'info':
        return `${baseClass} bg-blue-100 text-blue-800`
      default:
        return `${baseClass} bg-gray-100 text-gray-800`
    }
  }

  if (alerts.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <AlertTriangle className="h-12 w-12 mx-auto mb-2 opacity-30" />
        <p>No recent alerts</p>
      </div>
    )
  }

  return (
    <div className="space-y-3 max-h-96 overflow-y-auto scrollbar-thin">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className={`border-l-4 p-4 rounded-lg ${getSeverityColor(alert.severity)} transition-all hover:shadow-md`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                <AlertTriangle className="h-4 w-4" />
                <span className="font-semibold text-sm">{alert.well_id}</span>
                <span className={getSeverityBadge(alert.severity)}>
                  {alert.severity.toUpperCase()}
                </span>
              </div>
              <p className="text-sm font-medium mb-1">{alert.anomaly_type}</p>
              <p className="text-sm text-gray-700 mb-2">{alert.description}</p>
              <div className="flex items-center text-xs text-gray-500">
                <Clock className="h-3 w-3 mr-1" />
                {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default RecentAlerts

