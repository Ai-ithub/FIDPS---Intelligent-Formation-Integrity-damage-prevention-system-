import { useQuery } from 'react-query'
import { useWebSocketStore } from '../store/useWebSocketStore'
import { apiService } from '../services/api'
import MetricCard from '../components/Dashboard/MetricCard'
import SensorDataChart from '../components/Dashboard/SensorDataChart'
import AnomalyDistributionChart from '../components/Dashboard/AnomalyDistributionChart'
import RecentAlerts from '../components/Dashboard/RecentAlerts'

const Dashboard = () => {
  const { isConnected, metrics } = useWebSocketStore()

  // Fetch dashboard metrics
  const { data: dashboardData, isLoading } = useQuery(
    'dashboardMetrics',
    async () => {
      const response = await apiService.getDashboardMetrics()
      return response.data
    },
    {
      enabled: isConnected,
      refetchInterval: 30000,
    }
  )

  // Fetch recent anomalies
  const { data: recentAnomalies } = useQuery(
    'recentAnomalies',
    async () => {
      const response = await apiService.getActiveAnomalies({ limit: 10 })
      return response.data
    },
    {
      refetchInterval: 10000,
    }
  )

  const displayMetrics = isConnected ? metrics : dashboardData

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">Dashboard Overview</h2>
        <p className="text-gray-600 mt-2">Real-time monitoring of drilling operations</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Active Wells"
          value={displayMetrics?.active_wells || 0}
          icon="wells"
          trend={null}
          loading={isLoading}
        />
        <MetricCard
          title="Anomalies Today"
          value={displayMetrics?.total_anomalies_today || 0}
          icon="anomalies"
          trend={null}
          loading={isLoading}
        />
        <MetricCard
          title="Critical Alerts"
          value={displayMetrics?.critical_alerts || 0}
          icon="alerts"
          trend={null}
          loading={isLoading}
          alert={displayMetrics?.critical_alerts > 0}
        />
        <MetricCard
          title="Data Quality"
          value={`${displayMetrics?.data_quality_score?.toFixed(1) || 0}%`}
          icon="quality"
          trend={null}
          loading={isLoading}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Real-time Sensor Data</h3>
            <SensorDataChart />
          </div>
        </div>
        <div>
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Anomaly Distribution</h3>
            <AnomalyDistributionChart />
          </div>
        </div>
      </div>

      {/* Recent Alerts */}
      <div>
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Recent Alerts</h3>
          <RecentAlerts alerts={recentAnomalies || []} />
        </div>
      </div>
    </div>
  )
}

export default Dashboard

