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
  
  // MWD (Measurement While Drilling) sensors
  weight_on_bit?: number // Weight on bit in klbs
  rotary_speed?: number // Rotary speed in RPM
  torque?: number // Torque in ft-lbs
  flow_rate?: number // Flow rate in gpm
  standpipe_pressure?: number // Standpipe pressure in psi
  
  // LWD (Logging While Drilling) sensors
  gamma_ray?: number // Gamma ray reading in API units
  resistivity?: number // Resistivity in ohm-m
  neutron_porosity?: number // Neutron porosity in %
  bulk_density?: number // Bulk density in g/cm3
  photoelectric_factor?: number // Photoelectric factor
  
  // Drilling parameters
  rate_of_penetration?: number // Rate of penetration in ft/hr
  mud_weight?: number // Mud weight in ppg
  mud_temperature?: number // Mud temperature in °F
  
  // Pressure measurements
  pore_pressure?: number // Pore pressure in psi
  fracture_pressure?: number // Fracture pressure in psi
  equivalent_circulating_density?: number // ECD in ppg
  
  // Legacy fields (for backward compatibility)
  pressure?: number // Standpipe pressure (alias for standpipe_pressure)
  temperature?: number // Mud temperature (alias for mud_temperature)
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

