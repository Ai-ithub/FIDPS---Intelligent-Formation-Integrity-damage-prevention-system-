import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

interface DrillingParametersProps {
  rop: { value: number; average: number; timestamp: string }[]
  torque: { value: number; timestamp: string }[]
  drag: { value: number; timestamp: string }[]
  lwd: {
    gammaRay: number[]
    resistivity: { deep: number[]; shallow: number[] }
    depth: number[]
  } | null
}

const DrillingParameters = ({ rop, torque, drag, lwd }: DrillingParametersProps) => {
  const ropData = {
    labels: rop.map(r => new Date(r.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'ROP (ft/hr)',
        data: rop.map(r => r.value),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Average ROP',
        data: rop.map(r => r.average),
        borderColor: 'rgb(156, 163, 175)',
        backgroundColor: 'rgba(156, 163, 175, 0.1)',
        borderDash: [5, 5],
        tension: 0.4,
      },
    ],
  }

  const torqueData = {
    labels: torque.map(t => new Date(t.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'Torque (kft-lb)',
        data: torque.map(t => t.value),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4,
      },
    ],
  }

  const dragData = {
    labels: drag.map(d => new Date(d.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'Drag (klb)',
        data: drag.map(d => d.value),
        borderColor: 'rgb(234, 179, 8)',
        backgroundColor: 'rgba(234, 179, 8, 0.1)',
        tension: 0.4,
      },
    ],
  }

  const lwdData = lwd ? {
    labels: lwd.depth.map(d => `${d.toFixed(0)} m`),
    datasets: [
      {
        label: 'Gamma Ray (API)',
        data: lwd.gammaRay,
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        yAxisID: 'y',
        tension: 0.4,
      },
      {
        label: 'Resistivity Deep (ohm-m)',
        data: lwd.resistivity.deep,
        borderColor: 'rgb(168, 85, 247)',
        backgroundColor: 'rgba(168, 85, 247, 0.1)',
        yAxisID: 'y1',
        tension: 0.4,
      },
      {
        label: 'Resistivity Shallow (ohm-m)',
        data: lwd.resistivity.shallow,
        borderColor: 'rgb(249, 115, 22)',
        backgroundColor: 'rgba(249, 115, 22, 0.1)',
        yAxisID: 'y1',
        tension: 0.4,
      },
    ],
  } : null

  return (
    <div className="space-y-6">
      {/* ROP */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">Rate of Penetration (ROP)</h3>
        <div className="h-64">
          <Line data={ropData} options={{ responsive: true, maintainAspectRatio: false }} />
        </div>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-xs text-gray-500">Current ROP</div>
            <div className="text-xl font-semibold">{rop[rop.length - 1]?.value.toFixed(1)} ft/hr</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-xs text-gray-500">Average ROP</div>
            <div className="text-xl font-semibold">{rop[rop.length - 1]?.average.toFixed(1)} ft/hr</div>
          </div>
        </div>
      </div>

      {/* Torque & Drag */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Torque</h3>
          <div className="h-64">
            <Line data={torqueData} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
          <div className="mt-4 bg-red-50 p-3 rounded">
            <div className="text-xs text-gray-500">Current Torque</div>
            <div className="text-xl font-semibold">{torque[torque.length - 1]?.value.toFixed(1)} kft-lb</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Drag</h3>
          <div className="h-64">
            <Line data={dragData} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
          <div className="mt-4 bg-yellow-50 p-3 rounded">
            <div className="text-xs text-gray-500">Current Drag</div>
            <div className="text-xl font-semibold">{drag[drag.length - 1]?.value.toFixed(1)} klb</div>
          </div>
        </div>
      </div>

      {/* LWD Data */}
      {lwd && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">LWD Data</h3>
          <div className="h-96">
            <Line 
              data={lwdData} 
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  x: {
                    reverse: true,
                    title: { display: true, text: 'Depth (m)' },
                  },
                  y: {
                    position: 'left' as const,
                    title: { display: true, text: 'Gamma Ray (API)' },
                  },
                  y1: {
                    position: 'right' as const,
                    title: { display: true, text: 'Resistivity (ohm-m)' },
                    grid: { drawOnChartArea: false },
                  },
                },
              }} 
            />
          </div>
          <div className="mt-4 grid grid-cols-3 gap-4">
            <div className="bg-green-50 p-3 rounded">
              <div className="text-xs text-gray-500">Current Gamma Ray</div>
              <div className="text-xl font-semibold">{lwd.gammaRay[lwd.gammaRay.length - 1]?.toFixed(1)} API</div>
            </div>
            <div className="bg-purple-50 p-3 rounded">
              <div className="text-xs text-gray-500">Resistivity Deep</div>
              <div className="text-xl font-semibold">{lwd.resistivity.deep[lwd.resistivity.deep.length - 1]?.toFixed(2)} ohm-m</div>
            </div>
            <div className="bg-orange-50 p-3 rounded">
              <div className="text-xs text-gray-500">Resistivity Shallow</div>
              <div className="text-xl font-semibold">{lwd.resistivity.shallow[lwd.resistivity.shallow.length - 1]?.toFixed(2)} ohm-m</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DrillingParameters

