import { useState, useEffect } from 'react'
import { AlertTriangle, AlertCircle, Info, XCircle } from 'lucide-react'

interface Alert {
  id: string
  type: 'critical' | 'warning' | 'info'
  title: string
  message: string
  parameter: string
  currentValue: number
  threshold: number
  timestamp: string
  acknowledged: boolean
}

const AlertsPage = () => {
  const [alerts, setAlerts] = useState<Alert[]>([])

  useEffect(() => {
    // Initialize with sample alerts
    const sampleAlerts: Alert[] = [
      {
        id: '1',
        type: 'critical',
        title: 'Differential Pressure Increasing',
        message: 'Delta P is increasing rapidly. Risk of mechanical damage (particle invasion).',
        parameter: 'ΔP',
        currentValue: 185,
        threshold: 150,
        timestamp: new Date().toISOString(),
        acknowledged: false,
      },
      {
        id: '2',
        type: 'critical',
        title: 'Flow Out Decreased',
        message: 'Flow out dropped below 95%. Possible lost circulation (formation fracture).',
        parameter: 'Flow Out %',
        currentValue: 92,
        threshold: 95,
        timestamp: new Date(Date.now() - 300000).toISOString(),
        acknowledged: false,
      },
      {
        id: '3',
        type: 'warning',
        title: 'Torque Increasing',
        message: 'Torque is trending upward. Possible shale swelling indication.',
        parameter: 'Torque',
        currentValue: 15.2,
        threshold: 14,
        timestamp: new Date(Date.now() - 600000).toISOString(),
        acknowledged: false,
      },
      {
        id: '4',
        type: 'warning',
        title: 'HTHP Fluid Loss High',
        message: 'Last HTHP fluid loss test exceeded safe limits. Risk of chemical damage (clay swelling).',
        parameter: 'HTHP Fluid Loss',
        currentValue: 18.5,
        threshold: 15,
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        acknowledged: false,
      },
      {
        id: '5',
        type: 'info',
        title: 'ROP Decreased',
        message: 'Rate of penetration decreased. May indicate filter cake formation or pore plugging.',
        parameter: 'ROP',
        currentValue: 38,
        threshold: 40,
        timestamp: new Date(Date.now() - 900000).toISOString(),
        acknowledged: false,
      },
    ]

    setAlerts(sampleAlerts)

    // Simulate new alerts
    const interval = setInterval(() => {
      const newAlert: Alert = {
        id: Date.now().toString(),
        type: Math.random() > 0.7 ? 'critical' : Math.random() > 0.5 ? 'warning' : 'info',
        title: 'Parameter Alert',
        message: 'Parameter value outside normal range',
        parameter: 'Parameter',
        currentValue: Math.random() * 100,
        threshold: 50,
        timestamp: new Date().toISOString(),
        acknowledged: false,
      }
      setAlerts(prev => [newAlert, ...prev].slice(0, 20))
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const acknowledgeAlert = (id: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === id ? { ...alert, acknowledged: true } : alert
    ))
  }

  const getIcon = (type: string) => {
    switch (type) {
      case 'critical':
        return <XCircle className="h-6 w-6" />
      case 'warning':
        return <AlertTriangle className="h-6 w-6" />
      default:
        return <Info className="h-6 w-6" />
    }
  }

  const getColorClasses = (type: string) => {
    switch (type) {
      case 'critical':
        return 'bg-red-50 border-red-200 text-red-800'
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800'
    }
  }

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">Intelligent Alerts</h2>
        <p className="text-gray-600 mt-2">Real-time system alerts and warnings</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-red-600 font-medium">Critical Alerts</div>
              <div className="text-3xl font-bold text-red-700">
                {alerts.filter(a => a.type === 'critical' && !a.acknowledged).length}
              </div>
            </div>
            <XCircle className="h-12 w-12 text-red-400" />
          </div>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-yellow-600 font-medium">Warnings</div>
              <div className="text-3xl font-bold text-yellow-700">
                {alerts.filter(a => a.type === 'warning' && !a.acknowledged).length}
              </div>
            </div>
            <AlertTriangle className="h-12 w-12 text-yellow-400" />
          </div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-blue-600 font-medium">Info</div>
              <div className="text-3xl font-bold text-blue-700">
                {alerts.filter(a => a.type === 'info' && !a.acknowledged).length}
              </div>
            </div>
            <Info className="h-12 w-12 text-blue-400" />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {alerts.map(alert => (
          <div
            key={alert.id}
            className={`border rounded-lg p-4 ${getColorClasses(alert.type)} ${alert.acknowledged ? 'opacity-50' : ''}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                <div className={`mt-1 ${alert.type === 'critical' ? 'text-red-600' : alert.type === 'warning' ? 'text-yellow-600' : 'text-blue-600'}`}>
                  {getIcon(alert.type)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="font-semibold">{alert.title}</h3>
                    {alert.acknowledged && (
                      <span className="text-xs bg-white px-2 py-1 rounded">Acknowledged</span>
                    )}
                  </div>
                  <p className="text-sm mb-2">{alert.message}</p>
                  <div className="flex items-center space-x-4 text-xs">
                    <span>
                      <strong>Parameter:</strong> {alert.parameter}
                    </span>
                    <span>
                      <strong>Current:</strong> {alert.currentValue.toFixed(2)}
                    </span>
                    <span>
                      <strong>Threshold:</strong> {alert.threshold.toFixed(2)}
                    </span>
                    <span>
                      <strong>Time:</strong> {new Date(alert.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
              {!alert.acknowledged && (
                <button
                  onClick={() => acknowledgeAlert(alert.id)}
                  className="ml-4 px-4 py-2 bg-white rounded hover:bg-gray-100 transition-colors text-sm font-medium"
                >
                  Acknowledge
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AlertsPage

