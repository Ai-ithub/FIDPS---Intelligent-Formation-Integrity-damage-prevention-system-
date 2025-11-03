export interface Well {
  well_id: string
  is_active: boolean
  last_data_time: string
  data_points: number
}

export interface Anomaly {
  id: string
  well_id: string
  timestamp: string
  anomaly_type: string
  severity: 'critical' | 'warning' | 'info'
  confidence: number
  description: string
  status: 'active' | 'acknowledged' | 'resolved'
}

export interface SensorData {
  well_id: string
  timestamp: string
  depth: number
  weight_on_bit?: number
  rotary_speed?: number
  torque?: number
  flow_rate?: number
  standpipe_pressure?: number
}

export interface DashboardMetrics {
  active_wells: number
  total_anomalies_today: number
  critical_alerts: number
  data_quality_score: number
  system_health: 'healthy' | 'warning' | 'degraded' | 'critical'
}

export interface DamageType {
  id: string
  name: string
  description: string
}

export interface RTORecommendation {
  id: string
  timestamp: string
  damageType: string
  currentValues: Record<string, number>
  recommendedValues: Record<string, number>
  expectedImprovement: number
  riskReduction: number
  status: 'pending' | 'approved' | 'rejected'
}

