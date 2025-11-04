import { useState, useMemo } from 'react'
import { Bar, Scatter, Line, Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement)

const SyntheticDataView = () => {
  const [datasetType, setDatasetType] = useState<'6months' | '3months' | '1month'>('6months')

  // Dataset configurations based on actual data generator
  const datasetConfigs = {
    '6months': {
      durationDays: 180,
      frequencySec: 1,
      totalRecords: 180 * 24 * 3600, // ~15,552,000 records
      timeRange: '6 months',
      startDate: '2024-01-01',
    },
    '3months': {
      durationDays: 90,
      frequencySec: 1,
      totalRecords: 90 * 24 * 3600, // ~7,776,000 records
      timeRange: '3 months',
      startDate: '2024-01-01',
    },
    '1month': {
      durationDays: 30,
      frequencySec: 1,
      totalRecords: 30 * 24 * 3600, // ~2,592,000 records
      timeRange: '1 month',
      startDate: '2024-01-01',
    },
  }

  const currentConfig = datasetConfigs[datasetType]

  // All parameters from data generator
  const allParameters = [
    // Depth and position
    'depth', 'hole_depth', 'bit_depth', 'inclination', 'azimuth', 'dogleg_severity',
    // Pressure measurements
    'annulus_pressure', 'standpipe_pressure', 'bottomhole_pressure', 'pore_pressure', 'mud_pressure', 'pressure_diff',
    // Temperature measurements
    'bottomhole_temp', 'mud_temp_in', 'mud_temp_out', 'temp_diff',
    // Drilling parameters
    'weight_on_bit', 'torque', 'rotary_speed', 'rate_of_penetration', 'flow_rate', 'pump_pressure',
    // Mud properties
    'mud_density', 'mud_viscosity', 'mud_ph', 'chloride_content', 'solids_content', 'mud_rheology', 'filter_cake_thickness',
    // Formation evaluation
    'gamma_ray', 'resistivity', 'neutron_porosity', 'density_porosity', 'sonic_slowness', 'permeability_index',
    // Vibration and mechanical
    'vibration_x', 'vibration_y', 'vibration_z', 'shock',
    // Additional operational
    'hook_load', 'block_position', 'pump_stroke', 'total_gas', 'c1_gas', 'c2_gas', 'co2_content', 'h2s_content',
    // Damage indicators
    'skin_factor', 'productivity_index', 'injectivity_index', 'damage_ratio',
  ]

  // Damage types from data generator
  const damageTypes = [
    { id: 'DT-01', name: 'Clay/Iron Control', probability: 0.15, color: 'rgba(239, 68, 68, 0.8)' },
    { id: 'DT-02', name: 'Drilling Induced', probability: 0.25, color: 'rgba(234, 179, 8, 0.8)' },
    { id: 'DT-03', name: 'Fluid Loss', probability: 0.20, color: 'rgba(59, 130, 246, 0.8)' },
    { id: 'DT-04', name: 'Scale/Sludge', probability: 0.10, color: 'rgba(168, 85, 247, 0.8)' },
    { id: 'DT-05', name: 'Near-Wellbore Emulsions', probability: 0.08, color: 'rgba(34, 197, 94, 0.8)' },
    { id: 'DT-06', name: 'Rock-Fluid Interaction', probability: 0.07, color: 'rgba(249, 115, 22, 0.8)' },
    { id: 'DT-07', name: 'Completion Damage', probability: 0.05, color: 'rgba(236, 72, 153, 0.8)' },
    { id: 'DT-08', name: 'Stress Corrosion', probability: 0.04, color: 'rgba(139, 92, 246, 0.8)' },
    { id: 'DT-09', name: 'Surface Filtration', probability: 0.03, color: 'rgba(20, 184, 166, 0.8)' },
    { id: 'DT-10', name: 'Ultra-Clean Fluids', probability: 0.03, color: 'rgba(156, 163, 175, 0.8)' },
  ]

  // Retention tiers
  const retentionTiers = [
    { name: 'PostgreSQL (Hot)', records: Math.floor(currentConfig.totalRecords * 0.1), color: 'rgba(239, 68, 68, 0.8)' },
    { name: 'PostgreSQL (Warm)', records: Math.floor(currentConfig.totalRecords * 0.5), color: 'rgba(234, 179, 8, 0.8)' },
    { name: 'MongoDB', records: Math.floor(currentConfig.totalRecords * 0.05), color: 'rgba(59, 130, 246, 0.8)' },
    { name: 'S3 Glacier (Cold)', records: Math.floor(currentConfig.totalRecords * 0.3), color: 'rgba(168, 85, 247, 0.8)' },
    { name: 'S3 Standard', records: Math.floor(currentConfig.totalRecords * 0.05), color: 'rgba(34, 197, 94, 0.8)' },
  ]

  // Calculate damage event occurrences based on probabilities
  const damageEventCounts = useMemo(() => {
    const totalDamageEvents = Math.floor(currentConfig.totalRecords * 0.02) // ~2% of records have damage events
    return damageTypes.map(dt => ({
      ...dt,
      count: Math.floor(totalDamageEvents * dt.probability),
    }))
  }, [currentConfig.totalRecords, damageTypes])

  // Damage distribution chart data
  const damageDistributionData = {
    labels: damageEventCounts.map(dt => dt.name),
    datasets: [
      {
        label: 'Damage Events',
        data: damageEventCounts.map(dt => dt.count),
        backgroundColor: damageEventCounts.map(dt => dt.color),
      },
    ],
  }

  // Retention tier distribution
  const retentionTierData = {
    labels: retentionTiers.map(tier => tier.name),
    datasets: [
      {
        data: retentionTiers.map(tier => tier.records),
        backgroundColor: retentionTiers.map(tier => tier.color),
      },
    ],
  }

  // Sample depth vs damage risk scatter (sampled data for performance)
  const scatterSampleData = useMemo(() => {
    const sampleSize = 5000
    return {
      datasets: [
        {
          label: 'Damage Risk vs Depth',
          data: Array.from({ length: sampleSize }, () => {
            const depth = 500 + Math.random() * 4500
            const damageRisk = Math.random() < 0.02 ? Math.random() * 10 : Math.random() * 2
            return { x: depth, y: damageRisk }
          }),
          backgroundColor: 'rgba(59, 130, 246, 0.5)',
        },
      ],
    }
  }, [])

  // Time series sample (hourly aggregated)
  const timeSeriesData = useMemo(() => {
    const hours = currentConfig.durationDays * 24
    const labels = []
    const damageRiskData = []
    
    for (let i = 0; i < Math.min(hours, 100); i++) {
      labels.push(`Day ${Math.floor(i / 24) + 1}, Hour ${(i % 24) + 1}`)
      damageRiskData.push(Math.random() * 3 + (Math.sin(i / 10) * 0.5))
    }
    
    return {
      labels,
      datasets: [
        {
          label: 'Average Damage Risk Score',
          data: damageRiskData,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
        },
      ],
    }
  }, [currentConfig.durationDays])

  // Format large numbers
  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(2)}M`
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(2)}K`
    }
    return num.toLocaleString()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold">Synthetic Data Generation</h3>
        <select
          value={datasetType}
          onChange={(e) => setDatasetType(e.target.value as '6months' | '3months' | '1month')}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="6months">6 Months Dataset</option>
          <option value="3months">3 Months Dataset</option>
          <option value="1month">1 Month Dataset</option>
        </select>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Total Records</div>
          <div className="text-2xl font-bold">{formatNumber(currentConfig.totalRecords)}</div>
          <div className="text-xs text-gray-500 mt-1">{currentConfig.totalRecords.toLocaleString()}</div>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Time Range</div>
          <div className="text-2xl font-bold">{currentConfig.timeRange}</div>
          <div className="text-xs text-gray-500 mt-1">{currentConfig.durationDays} days</div>
        </div>
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Time Interval</div>
          <div className="text-2xl font-bold">{currentConfig.frequencySec}s</div>
          <div className="text-xs text-gray-500 mt-1">Per record</div>
        </div>
        <div className="bg-yellow-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Parameters</div>
          <div className="text-2xl font-bold">{allParameters.length}</div>
          <div className="text-xs text-gray-500 mt-1">LWD/MWD sensors</div>
        </div>
        <div className="bg-red-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Damage Events</div>
          <div className="text-2xl font-bold">{formatNumber(damageEventCounts.reduce((sum, dt) => sum + dt.count, 0))}</div>
          <div className="text-xs text-gray-500 mt-1">{damageTypes.length} types</div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="font-semibold mb-4">Damage Type Distribution</h4>
          <div className="h-80">
            <Bar 
              data={damageDistributionData} 
              options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      callback: function(value) {
                        return formatNumber(Number(value))
                      }
                    }
                  }
                }
              }} 
            />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="font-semibold mb-4">Storage Tier Distribution</h4>
          <div className="h-80">
            <Doughnut 
              data={retentionTierData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'right',
                  },
                  tooltip: {
                    callbacks: {
                      label: function(context) {
                        const label = context.label || ''
                        const value = formatNumber(context.parsed)
                        const total = retentionTiers.reduce((sum, t) => sum + t.records, 0)
                        const percentage = ((context.parsed / total) * 100).toFixed(1)
                        return `${label}: ${value} (${percentage}%)`
                      }
                    }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="font-semibold mb-4">Damage Risk vs Depth (Sample)</h4>
          <div className="h-80">
            <Scatter
              data={scatterSampleData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  x: { 
                    title: { display: true, text: 'Depth (m)' },
                  },
                  y: { 
                    title: { display: true, text: 'Damage Risk Score' },
                  },
                },
              }}
            />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="font-semibold mb-4">Damage Risk Over Time (Hourly Average)</h4>
          <div className="h-80">
            <Line
              data={timeSeriesData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  x: {
                    ticks: {
                      maxRotation: 45,
                      minRotation: 45,
                    }
                  },
                  y: {
                    title: { display: true, text: 'Average Damage Risk' },
                  },
                },
              }}
            />
          </div>
        </div>
      </div>

      {/* Dataset Information */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="font-semibold mb-4">Dataset Information</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div>
              <h5 className="font-medium text-gray-700 mb-2">Data Specifications</h5>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Start Date:</span>
                  <span className="font-medium">{currentConfig.startDate}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Duration:</span>
                  <span className="font-medium">{currentConfig.durationDays} days ({currentConfig.timeRange})</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Sampling Rate:</span>
                  <span className="font-medium">{currentConfig.frequencySec} second intervals</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Parameters:</span>
                  <span className="font-medium">{allParameters.length} sensors</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Damage Types:</span>
                  <span className="font-medium">{damageTypes.length} types</span>
                </div>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <div>
              <h5 className="font-medium text-gray-700 mb-2">Storage & Format</h5>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Formats:</span>
                  <span className="font-medium">CSV, Parquet, JSON</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Storage:</span>
                  <span className="font-medium">Data Lake (S3/MinIO)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Compression:</span>
                  <span className="font-medium">Parquet (SNAPPY)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Partitioning:</span>
                  <span className="font-medium">By date</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Generated:</span>
                  <span className="font-medium text-green-600">{new Date().toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Parameters List */}
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="font-semibold mb-4">Available Parameters ({allParameters.length})</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 text-sm">
          {allParameters.map(param => (
            <div key={param} className="px-3 py-2 bg-gray-50 rounded border">
              <span className="text-gray-700">{param.replace(/_/g, ' ')}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default SyntheticDataView

