import { useQuery } from 'react-query'
import { useWebSocketStore } from '../store/useWebSocketStore'
import { apiService } from '../services/api'
import MetricCard from '../components/Dashboard/MetricCard'
import SensorDataChart from '../components/Dashboard/SensorDataChart'
import AnomalyDistributionChart from '../components/Dashboard/AnomalyDistributionChart'
import RecentAlerts from '../components/Dashboard/RecentAlerts'
import PressureWindowChart from '../components/Dashboard/PressureWindowChart'
import DifferentialPressureGauge from '../components/Dashboard/DifferentialPressureGauge'
import FlowOutPercentage from '../components/Dashboard/FlowOutPercentage'
import MudParameters from '../components/Dashboard/MudParameters'
import DrillingFormationParams from '../components/Dashboard/DrillingFormationParams'
import IntelligentAlerts from '../components/Dashboard/IntelligentAlerts'

const Dashboard = () => {
  const { isConnected, metrics } = useWebSocketStore()

  // Fetch dashboard metrics (always enabled, not dependent on WebSocket)
  const { data: dashboardData, isLoading } = useQuery(
    'dashboardMetrics',
    async () => {
      try {
        const response = await apiService.getDashboardMetrics()
        return response.data
      } catch (error) {
        console.error('Error fetching dashboard metrics:', error)
        // Return mock data if API fails
        return {
          active_wells: 5,
          total_anomalies_today: 12,
          critical_alerts: 2,
          data_quality_score: 94.5,
          system_health: 'healthy',
        }
      }
    },
    {
      enabled: true, // Always fetch, even without WebSocket
      refetchInterval: 30000,
      retry: false, // Don't retry on error, use mock data
    }
  )

  // Fetch recent anomalies (always enabled)
  const { data: recentAnomalies } = useQuery(
    'recentAnomalies',
    async () => {
      try {
        const response = await apiService.getActiveAnomalies({ limit: 10 })
        return response.data
      } catch (error) {
        console.error('Error fetching recent anomalies:', error)
        // Return empty array if API fails
        return []
      }
    },
    {
      refetchInterval: 10000,
      retry: false, // Don't retry on error
    }
  )

  // Use WebSocket metrics if connected, otherwise use API data or default mock data
  const displayMetrics = isConnected && metrics.activeWells > 0 ? {
    active_wells: metrics.activeWells,
    total_anomalies_today: metrics.anomaliesToday,
    critical_alerts: metrics.criticalAlerts,
    data_quality_score: metrics.dataQualityScore,
    system_health: metrics.systemHealth,
  } : (dashboardData || {
    active_wells: 5,
    total_anomalies_today: 12,
    critical_alerts: 2,
    data_quality_score: 94.5,
    system_health: 'healthy',
  })

  return (
    <div className="space-y-6">
      <div>
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
          value={`${displayMetrics?.data_quality_score ? displayMetrics.data_quality_score.toFixed(1) : 0}%`}
          icon="quality"
          trend={null}
          loading={isLoading}
        />
      </div>

      {/* Section 1: Vital Indicators (KPIs) */}
      <div className="space-y-6">
        <div className="border-t pt-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">🩺</span>
            Section 1: Vital Indicators (KPIs) - Displayed in Largest Size
          </h2>
          <p className="text-gray-600 mb-6">These should act like "traffic lights". If any of these go outside the range, it means "danger".</p>

          {/* Pressure Window Chart */}
          <div className="mb-6">
            <PressureWindowChart />
          </div>

          {/* Differential Pressure Gauge */}
          <div className="mb-6">
            <DifferentialPressureGauge />
          </div>

          {/* Flow Out Percentage */}
          <div className="mb-6">
            <FlowOutPercentage />
          </div>
        </div>

        {/* Section 2: Mud Parameters */}
        <div className="border-t pt-6">
          <MudParameters />
        </div>

        {/* Section 3: Drilling & Formation Parameters */}
        <div className="border-t pt-6">
          <DrillingFormationParams />
        </div>

        {/* Section 4: Intelligent Alerts */}
        <div className="border-t pt-6">
          <IntelligentAlerts />
        </div>
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
          <RecentAlerts alerts={recentAnomalies || []} />
        </div>
      </div>
    </div>
  )
}

export default Dashboard

