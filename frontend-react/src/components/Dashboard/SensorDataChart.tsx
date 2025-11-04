import { useState, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale } from 'chart.js'
import 'chartjs-adapter-date-fns'
import { useWebSocketStore } from '../../store/useWebSocketStore'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
)

interface SensorConfig {
  key: string
  label: string
  color: string
  unit: string
  group: string
}

const SensorDataChart = () => {
  const { sensorData: wsSensorData } = useWebSocketStore()
  const [localSensorData, setLocalSensorData] = useState<any[]>([])

  // All sensors configuration
  const allSensors: SensorConfig[] = [
    // MWD Sensors
    { key: 'weight_on_bit', label: 'Weight on Bit', color: 'rgb(59, 130, 246)', unit: 'klbs', group: 'MWD Sensors' },
    { key: 'rotary_speed', label: 'Rotary Speed', color: 'rgb(34, 197, 94)', unit: 'RPM', group: 'MWD Sensors' },
    { key: 'torque', label: 'Torque', color: 'rgb(234, 179, 8)', unit: 'ft-lbs', group: 'MWD Sensors' },
    { key: 'flow_rate', label: 'Flow Rate', color: 'rgb(168, 85, 247)', unit: 'gpm', group: 'MWD Sensors' },
    { key: 'standpipe_pressure', label: 'Standpipe Pressure', color: 'rgb(239, 68, 68)', unit: 'psi', group: 'MWD Sensors' },
    
    // LWD Sensors
    { key: 'gamma_ray', label: 'Gamma Ray', color: 'rgb(236, 72, 153)', unit: 'API', group: 'LWD Sensors' },
    { key: 'resistivity', label: 'Resistivity', color: 'rgb(14, 165, 233)', unit: 'ohm-m', group: 'LWD Sensors' },
    { key: 'neutron_porosity', label: 'Neutron Porosity', color: 'rgb(249, 115, 22)', unit: '%', group: 'LWD Sensors' },
    { key: 'bulk_density', label: 'Bulk Density', color: 'rgb(20, 184, 166)', unit: 'g/cm³', group: 'LWD Sensors' },
    { key: 'photoelectric_factor', label: 'Photoelectric Factor', color: 'rgb(139, 92, 246)', unit: 'PEF', group: 'LWD Sensors' },
    
    // Drilling Parameters
    { key: 'rate_of_penetration', label: 'Rate of Penetration', color: 'rgb(59, 130, 246)', unit: 'ft/hr', group: 'Drilling Parameters' },
    { key: 'mud_weight', label: 'Mud Weight', color: 'rgb(34, 197, 94)', unit: 'ppg', group: 'Drilling Parameters' },
    { key: 'mud_temperature', label: 'Mud Temperature', color: 'rgb(239, 68, 68)', unit: '°F', group: 'Drilling Parameters' },
    
    // Pressure Measurements
    { key: 'pore_pressure', label: 'Pore Pressure', color: 'rgb(34, 197, 94)', unit: 'psi', group: 'Pressure Measurements' },
    { key: 'fracture_pressure', label: 'Fracture Pressure', color: 'rgb(239, 68, 68)', unit: 'psi', group: 'Pressure Measurements' },
    { key: 'equivalent_circulating_density', label: 'ECD', color: 'rgb(59, 130, 246)', unit: 'ppg', group: 'Pressure Measurements' },
  ]

  // Generate mock data if WebSocket data is not available
  useEffect(() => {
    if (wsSensorData && wsSensorData.length > 0) {
      setLocalSensorData(wsSensorData)
      return
    }

    // Generate sample data
    const now = new Date()
    const generateMockData = () => {
      const baseDepth = 1500 + Math.random() * 100
      return {
        timestamp: new Date().toISOString(),
        depth: baseDepth,
        
        // MWD sensors
        weight_on_bit: 15 + Math.random() * 10,
        rotary_speed: 100 + Math.random() * 50,
        torque: 3000 + Math.random() * 2000,
        flow_rate: 450 + Math.random() * 100,
        standpipe_pressure: 2500 + Math.random() * 500,
        
        // LWD sensors
        gamma_ray: 50 + Math.random() * 100,
        resistivity: 0.5 + Math.random() * 10,
        neutron_porosity: 10 + Math.random() * 30,
        bulk_density: 2.0 + Math.random() * 0.8,
        photoelectric_factor: 1.5 + Math.random() * 2.5,
        
        // Drilling parameters
        rate_of_penetration: 30 + Math.random() * 70,
        mud_weight: 9.2 + Math.random() * 1.5,
        mud_temperature: 180 + Math.random() * 40,
        
        // Pressure measurements
        pore_pressure: 2000 + Math.random() * 500,
        fracture_pressure: 3500 + Math.random() * 1000,
        equivalent_circulating_density: 9.5 + Math.random() * 1.0,
        
        // Legacy aliases
        pressure: 2500 + Math.random() * 500,
        temperature: 180 + Math.random() * 40,
      }
    }

    const initialData = Array.from({ length: 20 }, (_, i) => {
      const data = generateMockData()
      data.timestamp = new Date(now.getTime() - (20 - i) * 60000).toISOString()
      return data
    })
    setLocalSensorData(initialData)

    const interval = setInterval(() => {
      setLocalSensorData(prev => {
        const newData = generateMockData()
        newData.timestamp = new Date().toISOString()
        return [...prev.slice(1), newData]
      })
    }, 5000)

    return () => clearInterval(interval)
  }, [wsSensorData])

  const displayData = wsSensorData.length > 0 ? wsSensorData : localSensorData

  // Group sensors by category
  const groupedSensors = allSensors.reduce((acc, sensor) => {
    if (!acc[sensor.group]) {
      acc[sensor.group] = []
    }
    acc[sensor.group].push(sensor)
    return acc
  }, {} as Record<string, SensorConfig[]>)

  // Prepare chart data for a single sensor
  const getChartData = (sensor: SensorConfig) => {
    return {
      labels: displayData.map((d: any) => new Date(d.timestamp || d.t || Date.now())),
      datasets: [
        {
          label: `${sensor.label} (${sensor.unit})`,
          data: displayData.map((d: any) => {
            // Try sensor key first, then legacy aliases
            return d[sensor.key] || 
                   (sensor.key === 'standpipe_pressure' && d.pressure) ||
                   (sensor.key === 'mud_temperature' && d.temperature) ||
                   null
          }),
          borderColor: sensor.color,
          backgroundColor: sensor.color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
          tension: 0.1,
          borderWidth: 2,
          fill: true,
        },
      ],
    }
  }

  const chartOptions = (sensor: SensorConfig) => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 10,
          font: {
            size: 11,
          },
        },
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const label = context.dataset.label || ''
            const value = context.parsed.y !== null ? context.parsed.y.toFixed(2) : 'N/A'
            return `${label}: ${value}`
          },
        },
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: 'minute' as const,
          displayFormats: {
            minute: 'HH:mm',
          },
        },
        title: {
          display: false,
        },
        ticks: {
          maxTicksLimit: 6,
          font: {
            size: 10,
          },
        },
      },
      y: {
        beginAtZero: false,
        title: {
          display: true,
          text: sensor.unit,
          font: {
            size: 11,
          },
        },
      },
    },
  })

  return (
    <div className="space-y-6">
      {/* Display all sensors organized by groups */}
      {Object.entries(groupedSensors).map(([groupName, sensors]) => (
        <div key={groupName} className="space-y-4">
          {/* Group Header */}
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-3">
            <h4 className="text-base font-bold text-blue-900">{groupName}</h4>
          </div>

          {/* Charts Grid for this group */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sensors.map((sensor) => {
              const latestValue = displayData.length > 0 ? displayData[displayData.length - 1] : null
              const value = latestValue?.[sensor.key] || 
                           (sensor.key === 'standpipe_pressure' && latestValue?.pressure) ||
                           (sensor.key === 'mud_temperature' && latestValue?.temperature) ||
                           null
              
              return (
                <div key={sensor.key} className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <h5 className="font-semibold text-sm text-gray-700">{sensor.label}</h5>
                    {value !== null && (
                      <span className="text-xs font-bold px-2 py-1 rounded" style={{ color: sensor.color, backgroundColor: sensor.color.replace('rgb', 'rgba').replace(')', ', 0.1)') }}>
                        {value.toFixed(2)} {sensor.unit}
                      </span>
                    )}
                  </div>
                  <div className="h-48">
                    <Line data={getChartData(sensor)} options={chartOptions(sensor)} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}

      {/* Summary of all sensors */}
      {displayData.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <h5 className="font-semibold text-sm mb-3">Current Values Summary</h5>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
            {allSensors.map((sensor) => {
              const latestValue = displayData[displayData.length - 1]
              const value = latestValue?.[sensor.key] || 
                           (sensor.key === 'standpipe_pressure' && latestValue?.pressure) ||
                           (sensor.key === 'mud_temperature' && latestValue?.temperature) ||
                           null
              return (
                <div key={sensor.key} className="bg-white rounded p-2 border border-gray-200">
                  <div className="text-xs text-gray-500 mb-1 truncate">{sensor.label}</div>
                  <div className="text-sm font-bold" style={{ color: sensor.color }}>
                    {value !== null ? value.toFixed(2) : 'N/A'}
                  </div>
                  <div className="text-xs text-gray-400">{sensor.unit}</div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export default SensorDataChart

