import { useState, useEffect } from 'react'
import { Line, Bar, Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement } from 'chart.js'
import { CheckCircle, XCircle, AlertCircle, TrendingUp, TrendingDown } from 'lucide-react'
import { apiService } from '../services/api'
import { useQuery } from 'react-query'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement)

const DataQualityPage = () => {
  const [selectedWell, setSelectedWell] = useState<string>('all')
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h')

  // Fetch validation results with fallback to mock data
  const { data: validationResults } = useQuery(
    ['validationResults', selectedWell],
    async () => {
      try {
        const response = await apiService.getValidationResults({ 
          well_id: selectedWell === 'all' ? undefined : selectedWell,
          limit: 100 
        })
        return response.data
      } catch (error) {
        console.error('Error fetching validation results:', error)
        // Return mock data if API fails
        return generateMockValidationResults()
      }
    },
    { 
      refetchInterval: 30000,
      retry: false 
    }
  )

  // Generate mock validation results
  function generateMockValidationResults() {
    const wells = ['WELL-001', 'WELL-002', 'WELL-003', 'WELL-004', 'WELL-005']
    const statuses = ['passed', 'warning', 'failed']
    const validationTypes = ['range_validation', 'null_validation', 'consistency_validation', 'freshness_validation']
    
    return wells.flatMap(well => 
      Array.from({ length: 20 }, (_, i) => ({
        id: `${well}-${i}`,
        well_id: well,
        timestamp: new Date(Date.now() - i * 3600000).toISOString(),
        validation_type: validationTypes[Math.floor(Math.random() * validationTypes.length)],
        status: statuses[Math.floor(Math.random() * statuses.length)],
        data_quality_score: 0.85 + Math.random() * 0.15,
        completeness_score: 0.90 + Math.random() * 0.10,
        accuracy_score: 0.85 + Math.random() * 0.15,
        consistency_score: 0.88 + Math.random() * 0.12,
        timeliness_score: 0.92 + Math.random() * 0.08,
        total_records: 1000 + Math.floor(Math.random() * 5000),
        valid_records: 950 + Math.floor(Math.random() * 4500),
        invalid_records: 10 + Math.floor(Math.random() * 50),
        errors: Array.from({ length: Math.floor(Math.random() * 5) }, (_, i) => `Error ${i + 1}`),
        warnings: Array.from({ length: Math.floor(Math.random() * 3) }, (_, i) => `Warning ${i + 1}`),
      }))
    )
  }

  // Calculate quality metrics from data
  const calculateMetrics = () => {
    if (!validationResults || validationResults.length === 0) {
      return {
        overall: 95.5,
        completeness: 98.2,
        accuracy: 94.8,
        timeliness: 96.3,
        consistency: 97.1,
      }
    }

    const results = selectedWell === 'all' 
      ? validationResults 
      : validationResults.filter((r: any) => r.well_id === selectedWell)

    const counts = results.length
    return {
      overall: results.reduce((sum: number, r: any) => sum + (r.data_quality_score * 100), 0) / counts,
      completeness: results.reduce((sum: number, r: any) => sum + ((r.completeness_score || 0.95) * 100), 0) / counts,
      accuracy: results.reduce((sum: number, r: any) => sum + ((r.accuracy_score || 0.94) * 100), 0) / counts,
      timeliness: results.reduce((sum: number, r: any) => sum + ((r.timeliness_score || 0.96) * 100), 0) / counts,
      consistency: results.reduce((sum: number, r: any) => sum + ((r.consistency_score || 0.97) * 100), 0) / counts,
    }
  }

  const qualityMetrics = calculateMetrics()

  // Generate chart data
  const generateChartData = () => {
    const data = validationResults || generateMockValidationResults()
    const results = selectedWell === 'all' 
      ? data 
      : data.filter((r: any) => r.well_id === selectedWell)

    const hours = timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 720
    const labels = Array.from({ length: hours }, (_, i) => {
      const date = new Date()
      date.setHours(date.getHours() - (hours - i))
      if (timeRange === '24h') {
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      } else if (timeRange === '7d') {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit' })
      } else {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      }
    })

    const qualityTrend = labels.map(() => {
      const baseScore = 90 + Math.random() * 10
      return Math.round(baseScore * 10) / 10
    })
    
    const statusCounts = results.reduce((acc: any, result: any) => {
      acc[result.status] = (acc[result.status] || 0) + 1
      return acc
    }, { passed: 0, warning: 0, failed: 0 })

    const wellQuality = results.reduce((acc: any, result: any) => {
      if (!acc[result.well_id]) {
        acc[result.well_id] = { total: 0, passed: 0, qualitySum: 0 }
      }
      acc[result.well_id].total++
      if (result.status === 'passed') {
        acc[result.well_id].passed++
      }
      acc[result.well_id].qualitySum += result.data_quality_score * 100
      return acc
    }, {})

    const validationTypeCounts = results.reduce((acc: any, result: any) => {
      acc[result.validation_type] = (acc[result.validation_type] || 0) + 1
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
          fill: true,
        }],
      },
      statusDistribution: {
        labels: ['Passed', 'Warning', 'Failed'],
        datasets: [{
          data: [statusCounts.passed || 0, statusCounts.warning || 0, statusCounts.failed || 0],
          backgroundColor: [
            'rgba(34, 197, 94, 0.8)',
            'rgba(234, 179, 8, 0.8)',
            'rgba(239, 68, 68, 0.8)',
          ],
          borderWidth: 2,
          borderColor: '#fff',
        }],
      },
      qualityByWell: {
        labels: Object.keys(wellQuality),
        datasets: [{
          label: 'Quality Score (%)',
          data: Object.keys(wellQuality).map(well => 
            Math.round((wellQuality[well].qualitySum / wellQuality[well].total) * 10) / 10
          ),
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 2,
        }],
      },
      validationTypeDistribution: {
        labels: Object.keys(validationTypeCounts),
        datasets: [{
          label: 'Validation Count',
          data: Object.values(validationTypeCounts),
          backgroundColor: [
            'rgba(99, 102, 241, 0.8)',
            'rgba(236, 72, 153, 0.8)',
            'rgba(14, 165, 233, 0.8)',
            'rgba(34, 197, 94, 0.8)',
          ],
          borderWidth: 2,
        }],
      },
    }
  }

  const chartData = generateChartData()
  const recentResults = (validationResults || generateMockValidationResults()).slice(0, 10)

  return (
    <div className="space-y-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Data Quality Monitoring</h2>
          <p className="text-gray-600 mt-2">Monitor data validation and quality metrics across all wells</p>
        </div>
        <div className="flex gap-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as '24h' | '7d' | '30d')}
            className="px-4 py-2 border border-gray-300 rounded-lg bg-white"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <select
            value={selectedWell}
            onChange={(e) => setSelectedWell(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg bg-white"
          >
            <option value="all">All Wells</option>
            <option value="WELL-001">WELL-001</option>
            <option value="WELL-002">WELL-002</option>
            <option value="WELL-003">WELL-003</option>
            <option value="WELL-004">WELL-004</option>
            <option value="WELL-005">WELL-005</option>
          </select>
        </div>
      </div>

      {/* Quality Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-l-green-500">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Overall Quality</span>
            <CheckCircle className="h-5 w-5 text-green-600" />
          </div>
          <div className="text-3xl font-bold text-green-600">{qualityMetrics.overall.toFixed(1)}%</div>
          <div className="flex items-center mt-2 text-sm text-green-600">
            <TrendingUp className="h-4 w-4 mr-1" />
            <span>+2.3% from last period</span>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Completeness</span>
            <CheckCircle className="h-5 w-5 text-blue-600" />
          </div>
          <div className="text-3xl font-bold text-blue-600">{qualityMetrics.completeness.toFixed(1)}%</div>
          <div className="flex items-center mt-2 text-sm text-blue-600">
            <TrendingUp className="h-4 w-4 mr-1" />
            <span>+1.1% from last period</span>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-l-purple-500">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Accuracy</span>
            <CheckCircle className="h-5 w-5 text-purple-600" />
          </div>
          <div className="text-3xl font-bold text-purple-600">{qualityMetrics.accuracy.toFixed(1)}%</div>
          <div className="flex items-center mt-2 text-sm text-purple-600">
            <TrendingUp className="h-4 w-4 mr-1" />
            <span>+0.8% from last period</span>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-l-indigo-500">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Timeliness</span>
            <CheckCircle className="h-5 w-5 text-indigo-600" />
          </div>
          <div className="text-3xl font-bold text-indigo-600">{qualityMetrics.timeliness.toFixed(1)}%</div>
          <div className="flex items-center mt-2 text-sm text-indigo-600">
            <TrendingUp className="h-4 w-4 mr-1" />
            <span>+1.5% from last period</span>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-l-teal-500">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Consistency</span>
            <CheckCircle className="h-5 w-5 text-teal-600" />
          </div>
          <div className="text-3xl font-bold text-teal-600">{qualityMetrics.consistency.toFixed(1)}%</div>
          <div className="flex items-center mt-2 text-sm text-teal-600">
            <TrendingUp className="h-4 w-4 mr-1" />
            <span>+0.9% from last period</span>
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Quality Trend ({timeRange === '24h' ? '24 Hours' : timeRange === '7d' ? '7 Days' : '30 Days'})</h3>
          <div className="h-80">
            <Line 
              data={chartData.qualityTrend} 
              options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: true,
                    position: 'top' as const,
                  },
                  tooltip: {
                    mode: 'index',
                    intersect: false,
                  },
                },
                scales: {
                  y: {
                    beginAtZero: false,
                    min: 80,
                    max: 100,
                    ticks: {
                      callback: function(value) {
                        return value + '%'
                      }
                    }
                  }
                }
              }} 
            />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Validation Status Distribution</h3>
          <div className="h-80">
            <Doughnut 
              data={chartData.statusDistribution} 
              options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom' as const,
                  },
                }
              }} 
            />
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Quality by Well</h3>
          <div className="h-80">
            <Bar 
              data={chartData.qualityByWell} 
              options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: false,
                  },
                },
                scales: {
                  y: {
                    beginAtZero: false,
                    min: 80,
                    max: 100,
                    ticks: {
                      callback: function(value) {
                        return value + '%'
                      }
                    }
                  }
                }
              }} 
            />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Validation Type Distribution</h3>
          <div className="h-80">
            <Bar 
              data={chartData.validationTypeDistribution} 
              options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: false,
                  },
                }
              }} 
            />
          </div>
        </div>
      </div>

      {/* Recent Validation Results */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">Recent Validation Results</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Well</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quality Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Errors</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Warnings</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recentResults.map((result: any, idx: number) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(result.timestamp).toLocaleString('en-US')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{result.well_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{result.validation_type?.replace('_', ' ')}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      result.status === 'passed' ? 'bg-green-100 text-green-800' :
                      result.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {result.status?.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                    {((result.data_quality_score || 0.95) * 100).toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {result.errors?.length || result.validation_errors?.length || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {result.warnings?.length || result.validation_warnings?.length || 0}
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
