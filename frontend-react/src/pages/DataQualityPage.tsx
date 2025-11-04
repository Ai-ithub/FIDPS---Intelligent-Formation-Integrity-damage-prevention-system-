import { useState, useEffect } from 'react'
import { Line, Bar, Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement } from 'chart.js'
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { apiService } from '../services/api'
import { useQuery } from 'react-query'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement)

const DataQualityPage = () => {
  const [selectedWell, setSelectedWell] = useState<string>('all')

  // Fetch validation results
  const { data: validationResults } = useQuery(
    ['validationResults', selectedWell],
    () => apiService.getValidationResults({ 
      well_id: selectedWell === 'all' ? undefined : selectedWell,
      limit: 100 
    }),
    { refetchInterval: 30000 }
  )

  // Generate quality metrics
  const qualityMetrics = {
    overall: 95.5,
    completeness: 98.2,
    accuracy: 94.8,
    timeliness: 96.3,
    consistency: 97.1,
  }

  // Generate chart data
  const generateChartData = () => {
    if (!validationResults?.data) {
      return {
        qualityTrend: { labels: [], datasets: [] },
        statusDistribution: { labels: [], datasets: [] },
        qualityByWell: { labels: [], datasets: [] },
      }
    }

    const results = validationResults.data
    const labels = Array.from({ length: 24 }, (_, i) => {
      const date = new Date()
      date.setHours(date.getHours() - (24 - i))
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    })

    const qualityTrend = labels.map(() => 90 + Math.random() * 10)
    
    const statusCounts = results.reduce((acc: any, result: any) => {
      acc[result.status] = (acc[result.status] || 0) + 1
      return acc
    }, {})

    const wellQuality = results.reduce((acc: any, result: any) => {
      if (!acc[result.well_id]) {
        acc[result.well_id] = { total: 0, passed: 0 }
      }
      acc[result.well_id].total++
      if (result.status === 'passed') {
        acc[result.well_id].passed++
      }
      return acc
    }, {})

    return {
      qualityTrend: {
        labels,
        datasets: [{
          label: 'Data Quality Score (%)',
          data: qualityTrend,
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          tension: 0.4,
        }],
      },
      statusDistribution: {
        labels: Object.keys(statusCounts),
        datasets: [{
          data: Object.values(statusCounts),
          backgroundColor: [
            'rgba(34, 197, 94, 0.8)',
            'rgba(234, 179, 8, 0.8)',
            'rgba(239, 68, 68, 0.8)',
          ],
        }],
      },
      qualityByWell: {
        labels: Object.keys(wellQuality),
        datasets: [{
          label: 'Quality Score (%)',
          data: Object.keys(wellQuality).map(well => 
            (wellQuality[well].passed / wellQuality[well].total) * 100
          ),
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
        }],
      },
    }
  }

  const chartData = generateChartData()

  return (
    <div className="space-y-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Data Quality Monitoring</h2>
          <p className="text-gray-600 mt-2">Monitor data validation and quality metrics</p>
        </div>
        <select
          value={selectedWell}
          onChange={(e) => setSelectedWell(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="all">All Wells</option>
          <option value="WELL-001">WELL-001</option>
          <option value="WELL-002">WELL-002</option>
          <option value="WELL-003">WELL-003</option>
        </select>
      </div>

      {/* Quality Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Overall Quality</span>
            <CheckCircle className="h-5 w-5 text-green-600" />
          </div>
          <div className="text-3xl font-bold text-green-600">{qualityMetrics.overall.toFixed(1)}%</div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Completeness</span>
            <CheckCircle className="h-5 w-5 text-blue-600" />
          </div>
          <div className="text-3xl font-bold text-blue-600">{qualityMetrics.completeness.toFixed(1)}%</div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Accuracy</span>
            <CheckCircle className="h-5 w-5 text-purple-600" />
          </div>
          <div className="text-3xl font-bold text-purple-600">{qualityMetrics.accuracy.toFixed(1)}%</div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Timeliness</span>
            <CheckCircle className="h-5 w-5 text-indigo-600" />
          </div>
          <div className="text-3xl font-bold text-indigo-600">{qualityMetrics.timeliness.toFixed(1)}%</div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Consistency</span>
            <CheckCircle className="h-5 w-5 text-teal-600" />
          </div>
          <div className="text-3xl font-bold text-teal-600">{qualityMetrics.consistency.toFixed(1)}%</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Quality Trend (24 Hours)</h3>
          <div className="h-64">
            <Line data={chartData.qualityTrend} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Validation Status Distribution</h3>
          <div className="h-64">
            <Doughnut data={chartData.statusDistribution} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">Quality by Well</h3>
        <div className="h-64">
          <Bar data={chartData.qualityByWell} options={{ responsive: true, maintainAspectRatio: false }} />
        </div>
      </div>

      {/* Recent Validation Results */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">Recent Validation Results</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Well</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quality Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Errors</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Warnings</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {validationResults?.data?.slice(0, 10).map((result: any, idx: number) => (
                <tr key={idx}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(result.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{result.well_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{result.validation_type}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      result.status === 'passed' ? 'bg-green-100 text-green-800' :
                      result.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {result.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {(result.data_quality_score * 100).toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {result.errors?.length || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {result.warnings?.length || 0}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default DataQualityPage
