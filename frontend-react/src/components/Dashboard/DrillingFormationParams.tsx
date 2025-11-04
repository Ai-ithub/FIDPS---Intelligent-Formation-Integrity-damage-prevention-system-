import { TrendingUp, RotateCw, Gauge, Radio } from 'lucide-react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

interface DrillingFormationParamsProps {
  rop?: number // Rate of Penetration (ft/hr)
  ropAverage?: number // Average ROP
  torque?: number[] // Torque history (ft-lb)
  drag?: number[] // Drag history (lb)
  gammaRay?: number[] // Gamma Ray log data (API)
  shallowResistivity?: number[] // Shallow Resistivity (ohm-m)
  deepResistivity?: number[] // Deep Resistivity (ohm-m)
  depth?: number[] // Depth data (ft)
  lithology?: string // Current lithology
}

const DrillingFormationParams = ({
  rop = 45.5,
  ropAverage = 50.2,
  torque = Array.from({ length: 30 }, () => 8000 + Math.random() * 1000),
  drag = Array.from({ length: 30 }, () => 15000 + Math.random() * 2000),
  gammaRay = Array.from({ length: 50 }, (_, i) => 40 + Math.sin(i / 5) * 20),
  shallowResistivity = Array.from({ length: 50 }, () => 2 + Math.random() * 3),
  deepResistivity = Array.from({ length: 50 }, () => 2.5 + Math.random() * 4),
  depth = Array.from({ length: 50 }, (_, i) => 5000 + i * 10),
  lithology = 'Shale',
}: DrillingFormationParamsProps) => {
  const ropChange = ((rop - ropAverage) / ropAverage) * 100
  const ropTrend = rop < ropAverage * 0.7 // Significant drop

  // Torque/Drag chart data
  const torqueDragData = {
    labels: Array.from({ length: torque.length }, (_, i) => `T-${i + 1}`),
    datasets: [
      {
        label: 'Torque',
        data: torque,
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 2,
        tension: 0.1,
        yAxisID: 'y',
      },
      {
        label: 'Drag',
        data: drag,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        tension: 0.1,
        yAxisID: 'y1',
      },
    ],
  }

  const torqueDragOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Torque (ft-lb)',
        },
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Drag (lb)',
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  }

  // LWD data chart
  const lwdData = {
    labels: depth.map(d => `${d} ft`),
    datasets: [
      {
        label: 'Gamma Ray',
        data: gammaRay,
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 2,
        tension: 0.1,
        yAxisID: 'y',
      },
      {
        label: 'Resistivity (Shallow)',
        data: shallowResistivity,
        borderColor: 'rgb(234, 179, 8)',
        backgroundColor: 'rgba(234, 179, 8, 0.1)',
        borderWidth: 2,
        tension: 0.1,
        yAxisID: 'y1',
      },
      {
        label: 'Resistivity (Deep)',
        data: deepResistivity,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        tension: 0.1,
        yAxisID: 'y1',
      },
    ],
  }

  const lwdOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Depth (ft)',
        },
        reverse: true,
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Gamma Ray (API)',
        },
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Resistivity (ohm-m)',
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  }

  // Calculate resistivity separation (invasion indicator)
  const avgInvasion = deepResistivity.map((deep, i) => {
    const shallow = shallowResistivity[i]
    return deep > 0 && shallow > 0 ? ((deep - shallow) / shallow) * 100 : 0
  })
  const avgInvasionValue = avgInvasion.reduce((a, b) => a + b, 0) / avgInvasion.length

  return (
    <div className="space-y-6">
      <div className="flex items-center mb-4">
        <Gauge className="mr-2 h-6 w-6 text-purple-600" />
        <h2 className="text-2xl font-bold text-gray-900">Drilling & Formation Parameters</h2>
      </div>

      {/* ROP Display */}
      <div className={`card p-6 ${ropTrend ? 'border-l-4 border-l-yellow-500 bg-yellow-50' : ''}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <TrendingUp className="mr-2 h-5 w-5" />
            Rate of Penetration (ROP)
          </h3>
          {ropTrend && (
            <span className="status-badge status-warning">
              ⚠️ Significant ROP Decrease
            </span>
          )}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Current ROP</div>
            <div className="text-4xl font-bold text-blue-600">{rop.toFixed(1)}</div>
            <div className="text-sm text-gray-500 mt-1">ft/hr</div>
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Average ROP</div>
            <div className="text-4xl font-bold text-green-600">{ropAverage.toFixed(1)}</div>
            <div className="text-sm text-gray-500 mt-1">ft/hr</div>
            <div className={`mt-2 text-sm ${ropChange < 0 ? 'text-red-600' : 'text-green-600'}`}>
              {ropChange > 0 ? '+' : ''}{ropChange.toFixed(1)}% from average
            </div>
          </div>
        </div>
        {ropTrend && (
          <div className="mt-4 bg-yellow-100 border border-yellow-300 rounded-lg p-4">
            <div className="text-sm text-yellow-800 font-medium">
              ⚠️ Sudden and significant ROP decrease may indicate:
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Thick filter cake formation on formation face (due to high filtration)</li>
                <li>Pore plugging</li>
                <li>Both are signs of formation damage</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Torque and Drag */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <RotateCw className="mr-2 h-5 w-5" />
            Torque & Drag
          </h3>
        </div>
        <div className="h-80 mb-4">
          <Line data={torqueDragData} options={torqueDragOptions} />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Current Torque</div>
            <div className="text-2xl font-bold">{torque[torque.length - 1]?.toFixed(0)}</div>
            <div className="text-sm text-gray-500 mt-1">ft-lb</div>
            <div className="mt-2 text-xs text-gray-600">
              Average: {(torque.reduce((a, b) => a + b, 0) / torque.length).toFixed(0)} ft-lb
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Current Drag</div>
            <div className="text-2xl font-bold">{drag[drag.length - 1]?.toFixed(0)}</div>
            <div className="text-sm text-gray-500 mt-1">lb</div>
            <div className="mt-2 text-xs text-gray-600">
              Average: {(drag.reduce((a, b) => a + b, 0) / drag.length).toFixed(0)} lb
            </div>
          </div>
        </div>
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm text-blue-800">
            💡 Sudden increase in torque or drag may indicate shale swelling and wellbore narrowing, directly related to chemical damage.
          </div>
        </div>
      </div>

      {/* LWD Data */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Radio className="mr-2 h-5 w-5" />
            LWD Data (Logging While Drilling)
          </h3>
          <div className="bg-white rounded-lg px-3 py-1 border border-gray-200">
            <span className="text-sm font-medium text-gray-700">Current Lithology: </span>
            <span className="text-sm font-bold text-purple-600">{lithology}</span>
          </div>
        </div>
        <div className="h-96 mb-4">
          <Line data={lwdData} options={lwdOptions} />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Current Gamma Ray</div>
            <div className="text-2xl font-bold">{gammaRay[gammaRay.length - 1]?.toFixed(1)}</div>
            <div className="text-sm text-gray-500 mt-1">API</div>
            <div className="mt-2 text-xs text-gray-600">
              {lithology === 'Shale' ? (
                <span className="text-orange-600">⚠️ Shale: Swelling damage risk</span>
              ) : (
                <span className="text-blue-600">✓ Sand: Particle invasion risk</span>
              )}
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Resistivity (Shallow)</div>
            <div className="text-2xl font-bold">{shallowResistivity[shallowResistivity.length - 1]?.toFixed(2)}</div>
            <div className="text-sm text-gray-500 mt-1">ohm-m</div>
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Resistivity (Deep)</div>
            <div className="text-2xl font-bold">{deepResistivity[deepResistivity.length - 1]?.toFixed(2)}</div>
            <div className="text-sm text-gray-500 mt-1">ohm-m</div>
            <div className="mt-2 text-xs">
              Separation: <span className="font-bold">{avgInvasionValue.toFixed(1)}%</span>
            </div>
            {Math.abs(avgInvasionValue) > 10 && (
              <div className="mt-2 text-xs text-yellow-600">
                ⚠️ Significant separation: Indicates filtrate invasion into formation
              </div>
            )}
          </div>
        </div>
        <div className="mt-4 bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="text-sm text-purple-800 space-y-2">
            <div><strong>Gamma Ray:</strong> For lithology identification (shale, sand). Damage risk differs in shale (swelling) vs. sand (particle invasion).</div>
            <div><strong>Resistivity Separation:</strong> Separation between deep and shallow curves can indicate the degree of filtrate invasion into the formation.</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DrillingFormationParams
