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

type SensorGroup = 'mwd' | 'lwd' | 'drilling' | 'pressure'

interface SensorConfig {
  key: string
  label: string
  color: string
  unit: string
}

const SensorDataChart = () => {
  const { sensorData: wsSensorData } = useWebSocketStore()
  const [selectedGroup, setSelectedGroup] = useState<SensorGroup>('mwd')
  const [localSensorData, setLocalSensorData] = useState<any[]>([])

  // Sensor groups configuration
  const sensorGroups: Record<SensorGroup, { title: string; sensors: SensorConfig[] }> = {
    mwd: {
      title: 'MWD Sensors (Measurement While Drilling)',
      sensors: [
        { key: 'weight_on_bit', label: 'Weight on Bit', color: 'rgb(59, 130, 246)', unit: 'klbs' },
        { key: 'rotary_speed', label: 'Rotary Speed', color: 'rgb(34, 197, 94)', unit: 'RPM' },
        { key: 'torque', label: 'Torque', color: 'rgb(234, 179, 8)', unit: 'ft-lbs' },
        { key: 'flow_rate', label: 'Flow Rate', color: 'rgb(168, 85, 247)', unit: 'gpm' },
        { key: 'standpipe_pressure', label: 'Standpipe Pressure', color: 'rgb(239, 68, 68)', unit: 'psi' },
      ],
    },
    lwd: {
      title: 'LWD Sensors (Logging While Drilling)',
      sensors: [
        { key: 'gamma_ray', label: 'Gamma Ray', color: 'rgb(236, 72, 153)', unit: 'API' },
        { key: 'resistivity', label: 'Resistivity', color: 'rgb(14, 165, 233)', unit: 'ohm-m' },
        { key: 'neutron_porosity', label: 'Neutron Porosity', color: 'rgb(249, 115, 22)', unit: '%' },
        { key: 'bulk_density', label: 'Bulk Density', color: 'rgb(20, 184, 166)', unit: 'g/cm³' },
        { key: 'photoelectric_factor', label: 'Photoelectric Factor', color: 'rgb(139, 92, 246)', unit: 'PEF' },
      ],
    },
    drilling: {
      title: 'Drilling Parameters',
      sensors: [
        { key: 'rate_of_penetration', label: 'Rate of Penetration', color: 'rgb(59, 130, 246)', unit: 'ft/hr' },
        { key: 'mud_weight', label: 'Mud Weight', color: 'rgb(34, 197, 94)', unit: 'ppg' },
        { key: 'mud_temperature', label: 'Mud Temperature', color: 'rgb(239, 68, 68)', unit: '°F' },
      ],
    },
    pressure: {
      title: 'Pressure Measurements',
      sensors: [
        { key: 'pore_pressure', label: 'Pore Pressure', color: 'rgb(34, 197, 94)', unit: 'psi' },
        { key: 'fracture_pressure', label: 'Fracture Pressure', color: 'rgb(239, 68, 68)', unit: 'psi' },
        { key: 'equivalent_circulating_density', label: 'ECD', color: 'rgb(59, 130, 246)', unit: 'ppg' },
      ],
    },
  }

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

  const currentGroup = sensorGroups[selectedGroup]
  const displayData = wsSensorData.length > 0 ? wsSensorData : localSensorData

  // Prepare chart data for selected sensor group
  const chartData = {
    labels: displayData.map((d: any) => new Date(d.timestamp || d.t || Date.now())),
    datasets: currentGroup.sensors.map((sensor) => ({
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
    })),
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 15,
        },
      },
      title: {
        display: true,
        text: currentGroup.title,
        font: {
          size: 16,
          weight: 'bold' as const,
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
          display: true,
          text: 'Time',
        },
      },
      y: {
        beginAtZero: false,
        title: {
          display: true,
          text: 'Value',
        },
      },
    },
  }

  return (
    <div className="space-y-4">
      {/* Sensor Group Selector */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Sensor Group:</label>
          <select
            value={selectedGroup}
            onChange={(e) => setSelectedGroup(e.target.value as SensorGroup)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
          >
            <option value="mwd">MWD Sensors</option>
            <option value="lwd">LWD Sensors</option>
            <option value="drilling">Drilling Parameters</option>
            <option value="pressure">Pressure Measurements</option>
          </select>
        </div>
        {displayData.length > 0 && (
          <div className="text-sm text-gray-500">
            Last update: {new Date(displayData[displayData.length - 1]?.timestamp || Date.now()).toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="h-80 bg-gray-50 rounded-lg p-4 border border-gray-200">
        <Line data={chartData} options={options} />
      </div>

      {/* Current Values Display */}
      {displayData.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {currentGroup.sensors.map((sensor) => {
            const latestValue = displayData[displayData.length - 1]
            const value = latestValue?.[sensor.key] || 
                         (sensor.key === 'standpipe_pressure' && latestValue?.pressure) ||
                         (sensor.key === 'mud_temperature' && latestValue?.temperature) ||
                         null
            return (
              <div key={sensor.key} className="bg-white rounded-lg p-3 border border-gray-200 shadow-sm">
                <div className="text-xs text-gray-500 mb-1">{sensor.label}</div>
                <div className="text-lg font-bold" style={{ color: sensor.color }}>
                  {value !== null ? value.toFixed(2) : 'N/A'}
                </div>
                <div className="text-xs text-gray-400">{sensor.unit}</div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default SensorDataChart

