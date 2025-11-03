import { useEffect, useState } from 'react'
import { useQuery } from 'react-query'
import { useWebSocketStore } from '../store/useWebSocketStore'
import { apiService } from '../services/api'

interface GaugeValue {
  label: string
  value: number
  min: number
  max: number
  unit: string
}

const RealtimeMonitoringPage = () => {
  const { isConnected, metrics } = useWebSocketStore()
  const [gaugeValues, setGaugeValues] = useState<GaugeValue[]>([])

  // Fetch sensor data
  const { data: sensorData } = useQuery(
    'sensorData',
    async () => {
      const response = await apiService.getWells()
      return response.data
    },
    {
      refetchInterval: 2000,
    }
  )

  // Simulate gauge values
  useEffect(() => {
    const initializeGauges = () => {
      setGaugeValues([
        { label: 'Frequency', value: 0, min: 0, max: 100, unit: 'Hz' },
        { label: 'Absolute Pressure', value: 0, min: 0, max: 1000, unit: 'psi' },
        { label: 'Static Pressure', value: 0, min: 0, max: 1000, unit: 'psi' },
        { label: 'Dynamic Pressure', value: 0, min: 0, max: 1000, unit: 'psi' },
        { label: 'Pressure', value: 0, min: -100, max: 100, unit: 'psi' },
        { label: 'Temperature', value: 0, min: 0, max: 1000, unit: '°C' },
        { label: 'Flow Rate', value: 0, min: 0, max: 500, unit: 'gpm' },
        { label: 'Vibration', value: 0, min: 0, max: 100, unit: 'Hz' },
      ])
    }

    initializeGauges()

    const interval = setInterval(() => {
      setGaugeValues(prev => prev.map(gauge => ({
        ...gauge,
        value: Math.random() * (gauge.max - gauge.min) + gauge.min
      })))
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  const createGaugeSVG = (gauge: GaugeValue, index: number) => {
    const percentage = (gauge.value - gauge.min) / (gauge.max - gauge.min)
    const angle = percentage * 180 // 0-180 degrees
    const x1 = 100
    const y1 = 80
    const x2 = 100 + 60 * Math.cos(Math.PI * angle / 180)
    const y2 = 80 - 60 * Math.sin(Math.PI * angle / 180)

    return (
      <div key={index} className="bg-gray-800 p-4 rounded-lg">
        <h3 className="text-sm font-semibold text-green-400 mb-3 text-center">
          {gauge.label}
        </h3>
        <div className="relative h-40 w-full">
          <svg viewBox="0 0 200 100" className="w-full h-full">
            {/* Arc background */}
            <path
              d="M 20 80 A 60 60 0 0 1 180 80"
              fill="none"
              stroke="#374151"
              strokeWidth="4"
            />
            {/* Scale marks */}
            {Array.from({ length: 11 }).map((_, i) => {
              const angle = i * 18
              const x1_mark = 100 + 60 * Math.cos(Math.PI * angle / 180)
              const y1_mark = 80 - 60 * Math.sin(Math.PI * angle / 180)
              const x2_mark = 100 + 50 * Math.cos(Math.PI * angle / 180)
              const y2_mark = 80 - 50 * Math.sin(Math.PI * angle / 180)
              
              return (
                <line
                  key={i}
                  x1={x1_mark}
                  y1={y1_mark}
                  x2={x2_mark}
                  y2={y2_mark}
                  stroke="#6b7280"
                  strokeWidth="2"
                />
              )
            })}
            {/* Scale labels */}
            {[0, 2, 4, 6, 8, 10].map((i) => {
              const angle = i * 18
              const value = (gauge.max - gauge.min) * (i / 10) + gauge.min
              const x = 100 + 45 * Math.cos(Math.PI * angle / 180)
              const y = 80 - 45 * Math.sin(Math.PI * angle / 180)
              
              return (
                <text
                  key={i}
                  x={x}
                  y={y + 4}
                  fill="#9ca3af"
                  fontSize="10"
                  textAnchor="middle"
                >
                  {Math.floor(value)}
                </text>
              )
            })}
            {/* Needle */}
            <line
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="#ef4444"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </svg>
          {/* Value display */}
          <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 bg-white text-black px-4 py-2 rounded font-bold">
            {gauge.value.toFixed(1)}
          </div>
        </div>
        <p className="text-xs text-center text-gray-400 mt-2">
          {gauge.unit}
        </p>
      </div>
    )
  }

  return (
    <div className="p-6 bg-gray-900 min-h-screen">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-white">Real-Time Monitoring</h2>
        <p className="text-gray-400 mt-2">
          Live sensor data and parameter visualization
          {isConnected && (
            <span className="ml-2 text-green-400">● Connected</span>
          )}
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-800 p-4 rounded-lg border-l-4 border-blue-500">
          <p className="text-sm text-gray-400">Active Wells</p>
          <p className="text-2xl font-bold text-white">{metrics?.active_wells || 0}</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg border-l-4 border-green-500">
          <p className="text-sm text-gray-400">Data Quality</p>
          <p className="text-2xl font-bold text-white">
            {((metrics?.data_quality_score || 0) * 100).toFixed(1)}%
          </p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg border-l-4 border-orange-500">
          <p className="text-sm text-gray-400">Alerts</p>
          <p className="text-2xl font-bold text-white">
            {metrics?.critical_alerts || 0}
          </p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg border-l-4 border-purple-500">
          <p className="text-sm text-gray-400">System Health</p>
          <p className="text-2xl font-bold text-white capitalize">
            {metrics?.system_health || 'unknown'}
          </p>
        </div>
      </div>

      {/* Gauges Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {gaugeValues.map((gauge, index) => createGaugeSVG(gauge, index))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-4">
            Sensor Data Analysis
          </h3>
          <div className="bg-white p-4 rounded h-64 flex items-center justify-center">
            <p className="text-gray-500">Chart visualization will be added here</p>
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-4">
            Anomaly Distribution
          </h3>
          <div className="bg-white p-4 rounded h-64 flex items-center justify-center">
            <p className="text-gray-500">Histogram will be added here</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RealtimeMonitoringPage

