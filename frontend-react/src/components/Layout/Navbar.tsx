import { Activity, Wifi, WifiOff } from 'lucide-react'
import { useWebSocketStore } from '../../store/useWebSocketStore'
import { format } from 'date-fns'
import { useState, useEffect } from 'react'

const Navbar = () => {
  const { isConnected } = useWebSocketStore()
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const getSystemHealth = () => {
    return isConnected ? 'healthy' : 'critical'
  }

  const healthClasses = {
    healthy: 'text-green-600',
    warning: 'text-yellow-600',
    critical: 'text-red-600',
  }

  return (
    <nav className="bg-gradient-to-r from-primary-600 to-primary-800 text-white shadow-lg">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Activity className="h-8 w-8" />
            <div>
              <h1 className="text-2xl font-bold">FIDPS - Dashboard</h1>
              <p className="text-primary-200 text-sm">Formation Integrity Damage Prevention System</p>
            </div>
          </div>

          <div className="flex items-center space-x-6">
            {/* Connection Status */}
            <div className="flex items-center space-x-2">
              {isConnected ? (
                <Wifi className="h-5 w-5" />
              ) : (
                <WifiOff className="h-5 w-5" />
              )}
              <span className="text-sm">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            {/* System Health */}
            <div className="flex items-center space-x-2">
              <div className={`h-3 w-3 rounded-full ${healthClasses[getSystemHealth()]}`} />
              <span className="text-sm capitalize">{getSystemHealth()}</span>
            </div>

            {/* Current Time */}
            <div className="text-sm">
              {format(currentTime, 'yyyy-MM-dd HH:mm:ss')}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar

