import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Activity, TrendingUp, AlertCircle } from 'lucide-react'
import { Line, Bar } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'
import { apiService } from '../services/api'
import { useQuery } from 'react-query'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend)

interface WellData {
  well_id: string
  depth: number
  wob: number // Weight on Bit in klbs
  rop: number // Rate of Penetration in ft/hr
  mudWeight: number // Mud Weight in ppg
  torque: number // in kft-lb
  flowRate: number // in gpm
  pressure: number // in psi
  temperature: number // in degF
  isActive: boolean
  lastUpdate: string
  rigPower: number // 2000 HP for onshore
  rigType: string // Onshore
}

const WellsPage = () => {
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedWell, setSelectedWell] = useState<string | null>(null)
  const itemsPerPage = 10

  // Generate sample well data (10 wells per page, 10 pages = 100 wells)
  const generateWellData = (): WellData[] => {
    const wells: WellData[] = []
    for (let i = 1; i <= 100; i++) {
      wells.push({
        well_id: `WELL-${String(i).padStart(3, '0')}`,
        depth: 1000 + Math.random() * 2000,
        wob: 30 + Math.random() * 20,
        rop: 40 + Math.random() * 20,
        mudWeight: 9.0 + Math.random() * 1.5,
        torque: 10 + Math.random() * 5,
        flowRate: 400 + Math.random() * 100,
        pressure: 2500 + Math.random() * 500,
        temperature: 180 + Math.random() * 30,
        isActive: Math.random() > 0.3,
        lastUpdate: new Date(Date.now() - Math.random() * 3600000).toISOString(),
        rigPower: 2000,
        rigType: 'Onshore',
      })
    }
    return wells
  }

  const [wells] = useState<WellData[]>(generateWellData())

  // Get current page wells
  const currentWells = wells.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  // Get current well data (first well of current page)
  const currentWell = selectedWell 
    ? wells.find(w => w.well_id === selectedWell) 
    : currentWells[0]

  // Generate real-time chart data for current well
  const [chartData, setChartData] = useState({
    wob: Array.from({ length: 30 }, () => 30 + Math.random() * 20),
    rop: Array.from({ length: 30 }, () => 40 + Math.random() * 20),
    mudWeight: Array.from({ length: 30 }, () => 9.0 + Math.random() * 1.5),
    labels: Array.from({ length: 30 }, (_, i) => {
      const date = new Date()
      date.setMinutes(date.getMinutes() - (30 - i))
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    }),
  })

  useEffect(() => {
    if (!currentWell) return

    const interval = setInterval(() => {
      setChartData(prev => ({
        labels: [...prev.labels.slice(1), new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })],
        wob: [...prev.wob.slice(1), currentWell.wob + (Math.random() - 0.5) * 2],
        rop: [...prev.rop.slice(1), currentWell.rop + (Math.random() - 0.5) * 3],
        mudWeight: [...prev.mudWeight.slice(1), currentWell.mudWeight + (Math.random() - 0.5) * 0.1],
      }))
    }, 2000)

    return () => clearInterval(interval)
  }, [currentWell])

  const wobChartData = {
    labels: chartData.labels,
    datasets: [{
      label: 'WOB (klbs)',
      data: chartData.wob,
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.4,
    }],
  }

  const ropChartData = {
    labels: chartData.labels,
    datasets: [{
      label: 'ROP (ft/hr)',
      data: chartData.rop,
      borderColor: 'rgb(34, 197, 94)',
      backgroundColor: 'rgba(34, 197, 94, 0.1)',
      tension: 0.4,
    }],
  }

  const mudWeightChartData = {
    labels: chartData.labels,
    datasets: [{
      label: 'Mud Weight (ppg)',
      data: chartData.mudWeight,
      borderColor: 'rgb(239, 68, 68)',
      backgroundColor: 'rgba(239, 68, 68, 0.1)',
      tension: 0.4,
    }],
  }

  const totalPages = Math.ceil(wells.length / itemsPerPage)

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">Wells Management</h2>
        <p className="text-gray-600 mt-2">Manage and monitor all drilling wells (Onshore - 2000 HP)</p>
      </div>

      {/* Current Well Overview */}
      {currentWell && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-2xl font-bold text-gray-900">Current Well: {currentWell.well_id}</h3>
              <p className="text-gray-600 text-sm">
                {currentWell.rigType} Rig - {currentWell.rigPower} HP
                {currentWell.isActive && (
                  <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
                    Active
                  </span>
                )}
              </p>
            </div>
            <select
              value={selectedWell || currentWell.well_id}
              onChange={(e) => setSelectedWell(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg"
            >
              {currentWells.map(well => (
                <option key={well.well_id} value={well.well_id}>{well.well_id}</option>
              ))}
            </select>
          </div>

          {/* Key Parameters */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">WOB</div>
              <div className="text-2xl font-bold text-blue-600">{currentWell.wob.toFixed(1)} klbs</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">ROP</div>
              <div className="text-2xl font-bold text-green-600">{currentWell.rop.toFixed(1)} ft/hr</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Mud Weight</div>
              <div className="text-2xl font-bold text-red-600">{currentWell.mudWeight.toFixed(2)} ppg</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Depth</div>
              <div className="text-2xl font-bold text-purple-600">{currentWell.depth.toFixed(0)} m</div>
            </div>
          </div>

          {/* Real-time Charts */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h4 className="text-sm font-semibold mb-2">WOB (klbs)</h4>
              <div className="h-48">
                <Line data={wobChartData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }} />
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-2">ROP (ft/hr)</h4>
              <div className="h-48">
                <Line data={ropChartData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }} />
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-2">Mud Weight (ppg)</h4>
              <div className="h-48">
                <Line data={mudWeightChartData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }} />
              </div>
            </div>
          </div>

          {/* Additional Parameters */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-xs text-gray-600">Torque</div>
              <div className="text-lg font-semibold">{currentWell.torque.toFixed(1)} kft-lb</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-xs text-gray-600">Flow Rate</div>
              <div className="text-lg font-semibold">{currentWell.flowRate.toFixed(1)} gpm</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-xs text-gray-600">Pressure</div>
              <div className="text-lg font-semibold">{currentWell.pressure.toFixed(0)} psi</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-xs text-gray-600">Temperature</div>
              <div className="text-lg font-semibold">{currentWell.temperature.toFixed(1)} °F</div>
            </div>
          </div>
        </div>
      )}

      {/* Wells Table */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">All Wells</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Well ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Depth (m)</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">WOB (klbs)</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ROP (ft/hr)</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mud Weight (ppg)</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Update</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {currentWells.map((well) => (
                <tr
                  key={well.well_id}
                  className={`cursor-pointer hover:bg-gray-50 ${selectedWell === well.well_id ? 'bg-blue-50' : ''}`}
                  onClick={() => setSelectedWell(well.well_id)}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {well.well_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {well.isActive ? (
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs font-medium">
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {well.depth.toFixed(0)} m
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {well.wob.toFixed(1)} klbs
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {well.rop.toFixed(1)} ft/hr
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {well.mudWeight.toFixed(2)} ppg
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(well.lastUpdate).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-6">
          <div className="text-sm text-gray-600">
            Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, wells.length)} of {wells.length} wells
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <div className="flex items-center space-x-1">
              {Array.from({ length: Math.min(10, totalPages) }, (_, i) => {
                const page = i + 1
                return (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`px-3 py-1 rounded ${
                      currentPage === page
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {page}
                  </button>
                )
              })}
            </div>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WellsPage
