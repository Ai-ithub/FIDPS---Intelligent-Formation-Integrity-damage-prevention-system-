import { useState, useEffect } from 'react'
import { Line, Bar } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'
import { AlertTriangle, XCircle, Info } from 'lucide-react'
import { apiService } from '../services/api'
import { useQuery } from 'react-query'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend)

const AnomaliesPage = () => {
  const [timeRange, setTimeRange] = useState('7d')

  // Fetch anomaly history
  const { data: anomalyHistory } = useQuery(
    ['anomalyHistory', timeRange],
    () => apiService.getAnomalyHistory({ 
      start_time: new Date(Date.now() - (timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 1) * 24 * 60 * 60 * 1000).toISOString(),
      limit: 1000 
    }),
    { refetchInterval: 30000 }
  )

  // Generate chart data from historical anomalies
  const generateChartData = () => {
    if (!anomalyHistory?.data?.anomalies) {
      return {
        timeline: { labels: [], datasets: [] },
        bySeverity: { labels: [], datasets: [] },
        byType: { labels: [], datasets: [] },
      }
    }

    const anomalies = anomalyHistory.data.anomalies
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 1
    const labels = Array.from({ length: days }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - (days - i - 1))
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    })

    // Timeline chart
    const timelineData = labels.map(label => {
      const date = new Date(label)
      return anomalies.filter(a => {
        const anomalyDate = new Date(a.timestamp)
        return anomalyDate.toDateString() === date.toDateString()
      }).length
    })

    // By severity
    const severityCounts = anomalies.reduce((acc: any, anomaly: any) => {
      acc[anomaly.severity] = (acc[anomaly.severity] || 0) + 1
      return acc
    }, {})

    // By type
    const typeCounts = anomalies.reduce((acc: any, anomaly: any) => {
      acc[anomaly.anomaly_type] = (acc[anomaly.anomaly_type] || 0) + 1
      return acc
    }, {})

    return {
      timeline: {
        labels,
        datasets: [{
          label: 'Anomalies per Day',
          data: timelineData,
          borderColor: 'rgb(239, 68, 68)',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          tension: 0.4,
        }],
      },
      bySeverity: {
        labels: Object.keys(severityCounts),
        datasets: [{
          label: 'Anomalies by Severity',
          data: Object.values(severityCounts),
          backgroundColor: [
            'rgba(239, 68, 68, 0.8)',
            'rgba(234, 179, 8, 0.8)',
            'rgba(59, 130, 246, 0.8)',
            'rgba(156, 163, 175, 0.8)',
          ],
        }],
      },
      byType: {
        labels: Object.keys(typeCounts).slice(0, 10),
        datasets: [{
          label: 'Anomalies by Type',
          data: Object.values(typeCounts).slice(0, 10),
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
        }],
      },
    }
  }

  const chartData = generateChartData()

  // Fetch active anomalies
  const { data: activeAnomalies } = useQuery(
    'activeAnomalies',
    () => apiService.getActiveAnomalies({ limit: 20 }),
    { refetchInterval: 10000 }
  )

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="h-5 w-5 text-red-600" />
      case 'high':
        return <AlertTriangle className="h-5 w-5 text-orange-600" />
      case 'medium':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />
      default:
        return <Info className="h-5 w-5 text-blue-600" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Anomaly Management</h2>
          <p className="text-gray-600 mt-2">Track and analyze historical anomaly data</p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="1d">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-red-600 font-medium">Critical</div>
              <div className="text-3xl font-bold text-red-700">
                {activeAnomalies?.data?.filter((a: any) => a.severity === 'critical').length || 0}
              </div>
            </div>
            <XCircle className="h-12 w-12 text-red-400" />
          </div>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-yellow-600 font-medium">High</div>
              <div className="text-3xl font-bold text-yellow-700">
                {activeAnomalies?.data?.filter((a: any) => a.severity === 'high').length || 0}
              </div>
            </div>
            <AlertTriangle className="h-12 w-12 text-yellow-400" />
          </div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-blue-600 font-medium">Medium</div>
              <div className="text-3xl font-bold text-blue-700">
                {activeAnomalies?.data?.filter((a: any) => a.severity === 'medium').length || 0}
              </div>
            </div>
            <Info className="h-12 w-12 text-blue-400" />
          </div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600 font-medium">Total</div>
              <div className="text-3xl font-bold text-gray-700">
                {activeAnomalies?.data?.length || 0}
              </div>
            </div>
            <AlertTriangle className="h-12 w-12 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Anomaly Timeline</h3>
          <div className="h-64">
            <Line data={chartData.timeline} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Anomalies by Severity</h3>
          <div className="h-64">
            <Bar data={chartData.bySeverity} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">Anomalies by Type</h3>
        <div className="h-64">
          <Bar data={chartData.byType} options={{ responsive: true, maintainAspectRatio: false }} />
        </div>
      </div>

      {/* Active Anomalies List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">Active Anomalies</h3>
        <div className="space-y-3">
          {activeAnomalies?.data?.slice(0, 10).map((anomaly: any) => (
            <div
              key={anomaly.id}
              className={`border rounded-lg p-4 ${
                anomaly.severity === 'critical' ? 'border-red-200 bg-red-50' :
                anomaly.severity === 'high' ? 'border-orange-200 bg-orange-50' :
                anomaly.severity === 'medium' ? 'border-yellow-200 bg-yellow-50' :
                'border-blue-200 bg-blue-50'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  {getSeverityIcon(anomaly.severity)}
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-semibold">{anomaly.anomaly_type}</h4>
                      <span className={`text-xs px-2 py-1 rounded ${
                        anomaly.severity === 'critical' ? 'bg-red-200 text-red-800' :
                        anomaly.severity === 'high' ? 'bg-orange-200 text-orange-800' :
                        anomaly.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-blue-200 text-blue-800'
                      }`}>
                        {anomaly.severity}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{anomaly.description}</p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>Well: {anomaly.well_id}</span>
                      <span>Time: {new Date(anomaly.timestamp).toLocaleString()}</span>
                      <span>Confidence: {(anomaly.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default AnomaliesPage
