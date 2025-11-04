import { useState } from 'react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

interface SensorConfig {
  key: string
  label: string
  unit: string
  group: string
  color: string
  minValue: number
  maxValue: number
}

const HistoricalDataView = () => {
  const [dateRange, setDateRange] = useState({ start: '2024-01-01', end: '2024-01-31' })
  const [selectedParameter, setSelectedParameter] = useState('weight_on_bit')

  // All LWD/MWD sensors configuration
  const allSensors: SensorConfig[] = [
    // MWD Sensors
    { key: 'weight_on_bit', label: 'Weight on Bit', unit: 'klbs', group: 'MWD Sensors', color: 'rgb(59, 130, 246)', minValue: 15, maxValue: 45 },
    { key: 'rotary_speed', label: 'Rotary Speed', unit: 'RPM', group: 'MWD Sensors', color: 'rgb(34, 197, 94)', minValue: 100, maxValue: 200 },
    { key: 'torque', label: 'Torque', unit: 'ft-lbs', group: 'MWD Sensors', color: 'rgb(234, 179, 8)', minValue: 10, maxValue: 30 },
    { key: 'flow_rate', label: 'Flow Rate', unit: 'gpm', group: 'MWD Sensors', color: 'rgb(168, 85, 247)', minValue: 400, maxValue: 600 },
    { key: 'standpipe_pressure', label: 'Standpipe Pressure', unit: 'psi', group: 'MWD Sensors', color: 'rgb(239, 68, 68)', minValue: 2500, maxValue: 3500 },
    
    // LWD Sensors
    { key: 'gamma_ray', label: 'Gamma Ray', unit: 'API', group: 'LWD Sensors', color: 'rgb(236, 72, 153)', minValue: 50, maxValue: 150 },
    { key: 'resistivity', label: 'Resistivity', unit: 'ohm-m', group: 'LWD Sensors', color: 'rgb(14, 165, 233)', minValue: 1, maxValue: 100 },
    { key: 'neutron_porosity', label: 'Neutron Porosity', unit: '%', group: 'LWD Sensors', color: 'rgb(249, 115, 22)', minValue: 10, maxValue: 30 },
    { key: 'bulk_density', label: 'Bulk Density', unit: 'g/cm³', group: 'LWD Sensors', color: 'rgb(20, 184, 166)', minValue: 2.0, maxValue: 3.0 },
    { key: 'photoelectric_factor', label: 'Photoelectric Factor', unit: 'PEF', group: 'LWD Sensors', color: 'rgb(139, 92, 246)', minValue: 2, maxValue: 5 },
    
    // Drilling Parameters
    { key: 'rate_of_penetration', label: 'Rate of Penetration', unit: 'ft/hr', group: 'Drilling Parameters', color: 'rgb(59, 130, 246)', minValue: 20, maxValue: 50 },
    { key: 'mud_weight', label: 'Mud Weight', unit: 'ppg', group: 'Drilling Parameters', color: 'rgb(34, 197, 94)', minValue: 8.5, maxValue: 10.5 },
    { key: 'mud_temperature', label: 'Mud Temperature', unit: '°F', group: 'Drilling Parameters', color: 'rgb(239, 68, 68)', minValue: 150, maxValue: 200 },
    
    // Pressure Measurements
    { key: 'pore_pressure', label: 'Pore Pressure', unit: 'psi', group: 'Pressure Measurements', color: 'rgb(34, 197, 94)', minValue: 800, maxValue: 1200 },
    { key: 'fracture_pressure', label: 'Fracture Pressure', unit: 'psi', group: 'Pressure Measurements', color: 'rgb(239, 68, 68)', minValue: 1200, maxValue: 1800 },
    { key: 'equivalent_circulating_density', label: 'ECD', unit: 'ppg', group: 'Pressure Measurements', color: 'rgb(59, 130, 246)', minValue: 9.0, maxValue: 11.0 },
  ]

  // Group sensors by category
  const groupedSensors = allSensors.reduce((acc, sensor) => {
    if (!acc[sensor.group]) {
      acc[sensor.group] = []
    }
    acc[sensor.group].push(sensor)
    return acc
  }, {} as Record<string, SensorConfig[]>)

  // Get selected sensor config
  const selectedSensor = allSensors.find(s => s.key === selectedParameter) || allSensors[0]

  // Generate historical data for all sensors
  const generateHistoricalData = () => {
    const startDate = new Date(dateRange.start)
    const endDate = new Date(dateRange.end)
    const days = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)) || 31
    const data: Record<string, number>[] = []
    
    for (let i = 0; i < days; i++) {
      const date = new Date(startDate)
      date.setDate(startDate.getDate() + i)
      
      const dayData: Record<string, number> = {
        date: date.toISOString(),
      }
      
      // Generate data for all sensors
      allSensors.forEach(sensor => {
        const baseValue = (sensor.minValue + sensor.maxValue) / 2
        const variation = (sensor.maxValue - sensor.minValue) * 0.3
        const trend = Math.sin((i / days) * Math.PI * 2) * 0.1 // Cyclical trend
        const noise = (Math.random() - 0.5) * variation
        dayData[sensor.key] = baseValue + noise + (trend * variation)
      })
      
      data.push(dayData)
    }
    
    return data
  }

  const historicalData = generateHistoricalData()

  const chartData = {
    labels: historicalData.map(d => new Date(d.date).toLocaleDateString()),
    datasets: [
      {
        label: `${selectedSensor.label} (${selectedSensor.unit})`,
        data: historicalData.map(d => d[selectedParameter]),
        borderColor: selectedSensor.color,
        backgroundColor: selectedSensor.color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
        tension: 0.4,
        fill: true,
      },
    ],
  }

  // Calculate statistics for selected parameter
  const values = historicalData.map(d => d[selectedParameter])
  const avgValue = values.reduce((sum, v) => sum + v, 0) / values.length
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold">Historical Data Analysis</h3>
        <div className="flex items-center space-x-4">
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          />
          <span>to</span>
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4 mb-4">
          <label className="text-sm font-medium">Parameter:</label>
          <select
            value={selectedParameter}
            onChange={(e) => setSelectedParameter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg min-w-[300px]"
          >
            {Object.entries(groupedSensors).map(([group, sensors]) => (
              <optgroup key={group} label={group}>
                {sensors.map(sensor => (
                  <option key={sensor.key} value={sensor.key}>
                    {sensor.label} ({sensor.unit})
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>
        <div className="h-96">
          <Line data={chartData} options={{ responsive: true, maintainAspectRatio: false }} />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Average {selectedSensor.label}</div>
          <div className="text-2xl font-bold">
            {avgValue.toFixed(2)} {selectedSensor.unit}
          </div>
        </div>
        <div className="bg-red-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Minimum {selectedSensor.label}</div>
          <div className="text-2xl font-bold">
            {minValue.toFixed(2)} {selectedSensor.unit}
          </div>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Maximum {selectedSensor.label}</div>
          <div className="text-2xl font-bold">
            {maxValue.toFixed(2)} {selectedSensor.unit}
          </div>
        </div>
      </div>
    </div>
  )
}

export default HistoricalDataView

