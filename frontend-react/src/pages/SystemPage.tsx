import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, AlertCircle, Activity } from 'lucide-react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

interface ServiceStatus {
  name: string
  status: 'healthy' | 'degraded' | 'unhealthy'
  cpu: number
  memory: number
  uptime: number
}

const SystemPage = () => {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: 'API Dashboard', status: 'healthy', cpu: 45, memory: 60, uptime: 99.9 },
    { name: 'ML Service', status: 'healthy', cpu: 38, memory: 55, uptime: 99.8 },
    { name: 'Data Validation', status: 'healthy', cpu: 25, memory: 40, uptime: 99.9 },
    { name: 'RTO Service', status: 'degraded', cpu: 65, memory: 75, uptime: 98.5 },
    { name: 'Database', status: 'healthy', cpu: 30, memory: 50, uptime: 100 },
    { name: 'Kafka', status: 'healthy', cpu: 20, memory: 35, uptime: 99.9 },
  ])

  const [systemMetrics, setSystemMetrics] = useState({
    labels: Array.from({ length: 20 }, (_, i) => new Date(Date.now() - (20 - i) * 60000).toLocaleTimeString()),
    cpu: Array.from({ length: 20 }, () => 40 + Math.random() * 20),
    memory: Array.from({ length: 20 }, () => 50 + Math.random() * 20),
  })

  useEffect(() => {
    const interval = setInterval(() => {
      setSystemMetrics(prev => ({
        labels: [...prev.labels.slice(1), new Date().toLocaleTimeString()],
        cpu: [...prev.cpu.slice(1), 40 + Math.random() * 20],
        memory: [...prev.memory.slice(1), 50 + Math.random() * 20],
      }))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'degraded':
        return <AlertCircle className="h-5 w-5 text-yellow-600" />
      default:
        return <XCircle className="h-5 w-5 text-red-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      default:
        return 'bg-red-100 text-red-800 border-red-200'
    }
  }

  const chartData = {
    labels: systemMetrics.labels,
    datasets: [
      {
        label: 'CPU Usage (%)',
        data: systemMetrics.cpu,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Memory Usage (%)',
        data: systemMetrics.memory,
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4,
      },
    ],
  }

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">System Status</h2>
        <p className="text-gray-600 mt-2">Monitor system health and service status</p>
      </div>

      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">System Health</span>
            <Activity className="h-5 w-5 text-green-600" />
          </div>
          <div className="text-3xl font-bold text-green-600">98.5%</div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Active Services</span>
            <CheckCircle className="h-5 w-5 text-blue-600" />
          </div>
          <div className="text-3xl font-bold text-blue-600">{services.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Healthy Services</span>
            <CheckCircle className="h-5 w-5 text-green-600" />
          </div>
          <div className="text-3xl font-bold text-green-600">
            {services.filter(s => s.status === 'healthy').length}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Avg CPU Usage</span>
            <Activity className="h-5 w-5 text-purple-600" />
          </div>
          <div className="text-3xl font-bold text-purple-600">
            {Math.round(services.reduce((sum, s) => sum + s.cpu, 0) / services.length)}%
          </div>
        </div>
      </div>

      {/* System Metrics Chart */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">System Resource Usage</h3>
        <div className="h-64">
          <Line data={chartData} options={{ responsive: true, maintainAspectRatio: false }} />
        </div>
      </div>

      {/* Service Status Table */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">Service Status</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Service</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">CPU %</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Memory %</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uptime %</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {services.map((service, idx) => (
                <tr key={idx}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {service.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(service.status)}
                      <span className={`text-sm px-2 py-1 rounded ${getStatusColor(service.status)}`}>
                        {service.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <div className="w-full bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          className={`h-2 rounded-full ${service.cpu > 70 ? 'bg-red-500' : service.cpu > 50 ? 'bg-yellow-500' : 'bg-green-500'}`}
                          style={{ width: `${service.cpu}%` }}
                        />
                      </div>
                      <span>{service.cpu}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <div className="w-full bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          className={`h-2 rounded-full ${service.memory > 80 ? 'bg-red-500' : service.memory > 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
                          style={{ width: `${service.memory}%` }}
                        />
                      </div>
                      <span>{service.memory}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {service.uptime.toFixed(1)}%
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

export default SystemPage
