import { useState, useEffect } from 'react'
import { Line, Bar, Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement } from 'chart.js'
import { AlertTriangle, XCircle, Info } from 'lucide-react'
import { apiService } from '../services/api'
import { useQuery } from 'react-query'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement)

const AnomaliesPage = () => {
  const [timeRange, setTimeRange] = useState('7d')

  // Generate mock anomaly data
  const generateMockAnomalies = () => {
    const anomalyTypes = [
      'Pressure Surge', 'Temperature Anomaly', 'Flow Rate Deviation', 
      'Torque Spike', 'Mud Weight Fluctuation', 'Gas Influx',
      'Lost Circulation', 'Stuck Pipe Warning', 'Vibration Alert',
      'ECD Variation'
    ]
    const severities = ['critical', 'high', 'medium', 'low']
    const wells = ['WELL-001', 'WELL-002', 'WELL-003', 'WELL-004', 'WELL-005']
    
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 1
    const anomalies: any[] = []
    
    for (let i = 0; i < days * 10; i++) {
      const timestamp = new Date(Date.now() - Math.random() * days * 24 * 60 * 60 * 1000)
      anomalies.push({
        id: `anomaly-${i}`,
        well_id: wells[Math.floor(Math.random() * wells.length)],
        anomaly_type: anomalyTypes[Math.floor(Math.random() * anomalyTypes.length)],
        severity: severities[Math.floor(Math.random() * severities.length)],
        description: `${anomalyTypes[Math.floor(Math.random() * anomalyTypes.length)]} detected in well operations`,
        timestamp: timestamp.toISOString(),
        confidence: 0.75 + Math.random() * 0.25,
        status: Math.random() > 0.3 ? 'active' : 'resolved',
      })
    }
    
    return anomalies
  }

  // Fetch anomaly history with fallback to mock data
  const { data: anomalyHistory } = useQuery(
    ['anomalyHistory', timeRange],
    async () => {
      try {
        const response = await apiService.getAnomalyHistory({ 
          start_time: new Date(Date.now() - (timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 1) * 24 * 60 * 60 * 1000).toISOString(),
          limit: 1000 
        })
        return response.data
      } catch (error) {
        console.error('Error fetching anomaly history:', error)
        return { anomalies: generateMockAnomalies() }
      }
    },
    { 
      refetchInterval: 30000,
      retry: false 
    }
  )

  // Generate chart data from historical anomalies
  const generateChartData = () => {
    const anomalies = anomalyHistory?.anomalies || generateMockAnomalies()
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 1
    const labels = Array.from({ length: days }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - (days - i - 1))
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    })

    // Timeline chart - anomalies per day
    const timelineData = labels.map((label, idx) => {
      const date = new Date()
      date.setDate(date.getDate() - (days - idx - 1))
      return anomalies.filter((a: any) => {
        const anomalyDate = new Date(a.timestamp)
        return anomalyDate.toDateString() === date.toDateString()
      }).length
    })

    // By severity
    const severityCounts = anomalies.reduce((acc: any, anomaly: any) => {
      acc[anomaly.severity] = (acc[anomaly.severity] || 0) + 1
      return acc
    }, { critical: 0, high: 0, medium: 0, low: 0 })

    // By type
    const typeCounts = anomalies.reduce((acc: any, anomaly: any) => {
      acc[anomaly.anomaly_type] = (acc[anomaly.anomaly_type] || 0) + 1
      return acc
    }, {})

    // Trend data (last 24 hours for hourly breakdown)
    const hourlyLabels = Array.from({ length: 24 }, (_, i) => {
      const date = new Date()
      date.setHours(date.getHours() - (24 - i))
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    })
    const hourlyData = hourlyLabels.map((label, idx) => {
      const date = new Date()
      date.setHours(date.getHours() - (24 - idx))
      return anomalies.filter((a: any) => {
        const anomalyDate = new Date(a.timestamp)
        return anomalyDate.getHours() === date.getHours() && 
               anomalyDate.toDateString() === date.toDateString()
      }).length
    })

    return {
      timeline: {
        labels,
        datasets: [{
          label: 'Anomalies per Day',
          data: timelineData,
          borderColor: 'rgb(239, 68, 68)',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          tension: 0.4,
          fill: true,
        }],
      },
      hourlyTrend: {
        labels: hourlyLabels,
        datasets: [{
          label: 'Anomalies per Hour (Last 24h)',
          data: hourlyData,
          borderColor: 'rgb(234, 179, 8)',
          backgroundColor: 'rgba(234, 179, 8, 0.1)',
          tension: 0.4,
          fill: true,
        }],
      },
      bySeverity: {
        labels: ['Critical', 'High', 'Medium', 'Low'],
        datasets: [{
          label: 'Anomalies by Severity',
          data: [
            severityCounts.critical || 0,
            severityCounts.high || 0,
            severityCounts.medium || 0,
            severityCounts.low || 0,
          ],
          backgroundColor: [
            'rgba(239, 68, 68, 0.8)',
            'rgba(234, 179, 8, 0.8)',
            'rgba(59, 130, 246, 0.8)',
            'rgba(156, 163, 175, 0.8)',
          ],
          borderWidth: 2,
          borderColor: '#fff',
        }],
      },
      byType: {
        labels: Object.keys(typeCounts).slice(0, 10),
        datasets: [{
          label: 'Anomalies by Type',
          data: Object.values(typeCounts).slice(0, 10) as number[],
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 2,
        }],
      },
      severityDistribution: {
        labels: ['Critical', 'High', 'Medium', 'Low'],
        datasets: [{
          data: [
            severityCounts.critical || 0,
            severityCounts.high || 0,
            severityCounts.medium || 0,
            severityCounts.low || 0,
          ],
          backgroundColor: [
            'rgba(239, 68, 68, 0.8)',
            'rgba(234, 179, 8, 0.8)',
            'rgba(59, 130, 246, 0.8)',
            'rgba(156, 163, 175, 0.8)',
          ],
          borderWidth: 2,
          borderColor: '#fff',
        }],
      },
    }
  }

  const chartData = generateChartData()

  // Fetch active anomalies with fallback to mock data
  const { data: activeAnomalies } = useQuery(
    'activeAnomalies',
    async () => {
      try {
        const response = await apiService.getActiveAnomalies({ limit: 20 })
        return response.data
      } catch (error) {
        console.error('Error fetching active anomalies:', error)
        const mockAnomalies = generateMockAnomalies()
        return { data: mockAnomalies.filter((a: any) => a.status === 'active').slice(0, 20) }
      }
    },
    { 
      refetchInterval: 10000,
      retry: false 
    }
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

  const anomalies = activeAnomalies?.data || generateMockAnomalies().filter((a: any) => a.status === 'active').slice(0, 10)

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
          className="px-4 py-2 border border-gray-300 rounded-lg bg-white"
        >
          <option value="1d">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 border-l-4 border-l-red-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-red-600 font-medium">Critical</div>
              <div className="text-3xl font-bold text-red-700">
                {anomalies.filter((a: any) => a.severity === 'critical').length}
              </div>
              <div className="text-xs text-red-600 mt-1">Requires immediate action</div>
            </div>
            <XCircle className="h-12 w-12 text-red-400" />
          </div>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 border-l-4 border-l-yellow-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-yellow-600 font-medium">High</div>
              <div className="text-3xl font-bold text-yellow-700">
                {anomalies.filter((a: any) => a.severity === 'high').length}
              </div>
              <div className="text-xs text-yellow-600 mt-1">Monitor closely</div>
            </div>
            <AlertTriangle className="h-12 w-12 text-yellow-400" />
          </div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-blue-600 font-medium">Medium</div>
              <div className="text-3xl font-bold text-blue-700">
                {anomalies.filter((a: any) => a.severity === 'medium').length}
              </div>
              <div className="text-xs text-blue-600 mt-1">Standard monitoring</div>
            </div>
            <Info className="h-12 w-12 text-blue-400" />
          </div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 border-l-4 border-l-gray-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600 font-medium">Total Active</div>
              <div className="text-3xl font-bold text-gray-700">
                {anomalies.length}
              </div>
              <div className="text-xs text-gray-600 mt-1">All severity levels</div>
            </div>
            <AlertTriangle className="h-12 w-12 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Anomaly Timeline ({timeRange === '1d' ? 'Last 24 Hours' : timeRange === '7d' ? 'Last 7 Days' : 'Last 30 Days'})</h3>
          <div className="h-80">
            <Line 
              data={chartData.timeline} 
              options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: true,
                    position: 'top' as const,
                  },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      stepSize: 1,
                    }
                  }
                }
              }} 
            />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Severity Distribution</h3>
          <div className="h-80">
            <Doughnut 
              data={chartData.severityDistribution} 
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
          <h3 className="text-lg font-semibold mb-4">Hourly Trend (Last 24 Hours)</h3>
          <div className="h-80">
            <Line 
              data={chartData.hourlyTrend} 
              options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: true,
                    position: 'top' as const,
                  },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      stepSize: 1,
                    }
                  }
                }
              }} 
            />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Anomalies by Severity</h3>
          <div className="h-80">
            <Bar 
              data={chartData.bySeverity} 
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
                    beginAtZero: true,
                    ticks: {
                      stepSize: 1,
                    }
                  }
                }
              }} 
            />
          </div>
        </div>
      </div>

      {/* Charts Row 3 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">Top Anomaly Types</h3>
        <div className="h-80">
          <Bar 
            data={chartData.byType} 
            options={{ 
              responsive: true, 
              maintainAspectRatio: false,
              indexAxis: 'y' as const,
              plugins: {
                legend: {
                  display: false,
                },
              },
              scales: {
                x: {
                  beginAtZero: true,
                  ticks: {
                    stepSize: 1,
                  }
                }
              }
            }} 
          />
        </div>
      </div>

      {/* Active Anomalies List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">Active Anomalies ({anomalies.length})</h3>
        <div className="space-y-3">
          {anomalies.slice(0, 15).map((anomaly: any, idx: number) => (
            <div
              key={anomaly.id || idx}
              className={`border rounded-lg p-4 transition-all hover:shadow-md ${
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
                      <h4 className="font-semibold text-gray-900">{anomaly.anomaly_type}</h4>
                      <span className={`text-xs px-2 py-1 rounded font-medium ${
                        anomaly.severity === 'critical' ? 'bg-red-200 text-red-800' :
                        anomaly.severity === 'high' ? 'bg-orange-200 text-orange-800' :
                        anomaly.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-blue-200 text-blue-800'
                      }`}>
                        {anomaly.severity?.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{anomaly.description}</p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span className="font-medium">Well: {anomaly.well_id}</span>
                      <span>Time: {new Date(anomaly.timestamp).toLocaleString('en-US')}</span>
                      <span>Confidence: {((anomaly.confidence || 0.85) * 100).toFixed(1)}%</span>
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
